"""Parse campaign summaries and channel activity without mixing their grain."""

from dataclasses import dataclass
from io import BytesIO
import re
import zipfile

import numpy as np
import pandas as pd


class UploadError(ValueError):
    pass


def token(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


ALIASES = {
    "survey_type": ["surveytype", "survey_type"],
    "campaign": ["campaign", "campaignname", "campaigndetails"],
    "task": ["task"],
    "channel": ["channel", "outreachchannel"],
    "start_date": ["start", "startdate"],
    "end_date": ["end", "enddate"],
    "year": ["year", "calendaryear"],
    "target_outreach": ["targetoutreach", "initialidentifiedoutreach"],
    "attempted_outreach": ["attemptedoutreach", "outreachattempts"],
    "outreach_fail": ["outreachfail", "outreachfailed"],
    "actual_outreach": ["actualoutreach", "successfuloutreach"],
    "responses": ["actualresponses", "responses", "responsecount"],
    "bulk_close": ["bulkclose", "bulkclosure", "bulkclosures"],
    "cost": ["cost", "campaigncost"],
    "reported_outreach": ["outreachratekpi1", "outreachrate", "outreachratepercentage"],
    "reported_response": ["responseratekpi2", "responserate", "responseratepercentage"],
    "reported_bulk": ["bulkcloseratekpi3", "bulkclosurerate", "bulkcloserate"],
}
LOOKUP = {token(alias): field for field, aliases in ALIASES.items() for alias in aliases}
NUMERIC = [
    "target_outreach",
    "attempted_outreach",
    "outreach_fail",
    "actual_outreach",
    "responses",
    "bulk_close",
    "cost",
    "reported_outreach",
    "reported_response",
    "reported_bulk",
]
CHANNELS = {
    "emailcampaign": "Email campaign",
    "customemails": "Custom emails",
    "callogixeffort": "Call Logic support",
    "calllogicsupport": "Call Logic support",
    "lettercampaign": "Letter campaign",
    "dentalteameffort": "Dental team effort",
    "ubemailcampaign": "UB email campaign",
    "groupemailcampaign": "Group email campaign",
}


@dataclass
class Dataset:
    campaigns: pd.DataFrame
    channels: pd.DataFrame
    issues: list[str]
    sheets: list[str]


def number(value):
    if pd.isna(value) or str(value).strip() in {"", "-", "N/A", "NA"}:
        return np.nan
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
    except ValueError:
        return np.nan


def date(value):
    if pd.isna(value):
        return pd.NaT
    if isinstance(value, (int, float)):
        return pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")
    return pd.to_datetime(value, errors="coerce")


def _tables(raw):
    """Find repeated header blocks, including title/blank rows in Excel."""
    starts = []
    for i, row in raw.iterrows():
        fields = {LOOKUP.get(token(v)) for v in row if pd.notna(v)}
        if "survey_type" in fields and fields.intersection({"task", "campaign"}):
            starts.append(i)
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(raw)
        names = [LOOKUP.get(token(v), f"unused_{j}") for j, v in enumerate(raw.iloc[start])]
        if len(names) != len(set(names)):
            raise UploadError("Ambiguous duplicate column headers. Use one column per field.")
        table = raw.iloc[start + 1 : end].copy()
        table.columns = names
        yield table


def load_upload(content: bytes, filename: str) -> Dataset:
    if len(content) > 20 * 1024 * 1024:
        raise UploadError("Upload must be at most 20 MB.")
    extension = filename.rsplit(".", 1)[-1].lower()
    try:
        if extension == "csv":
            try:
                raw = pd.read_csv(BytesIO(content), header=None, encoding="utf-8-sig")
            except UnicodeDecodeError:
                raw = pd.read_csv(BytesIO(content), header=None, encoding="cp1252")
            sheets = {"CSV": raw}
        elif extension in {"xlsx", "xls"}:
            if extension == "xlsx":
                with zipfile.ZipFile(BytesIO(content)) as archive:
                    if sum(e.file_size for e in archive.infolist()) > 100 * 1024 * 1024:
                        raise UploadError("Expanded workbook exceeds the 100 MB safety limit.")
            sheets = pd.read_excel(BytesIO(content), sheet_name=None, header=None)
        else:
            raise UploadError("Choose a CSV, XLSX, or XLS file.")
    except UploadError:
        raise
    except Exception as exc:
        raise UploadError("Cannot read this file. Check its format and remove password protection.") from exc

    summaries, activities, issues, accepted = [], [], [], []
    for sheet, raw in sheets.items():
        tables = list(_tables(raw))
        if not tables:
            issues.append(f"Skipped '{sheet}': no supported campaign header found.")
            continue
        accepted.append(sheet)
        for table in tables:
            current = None
            for row_index, row in table.iterrows():
                if pd.isna(row.get("survey_type")):
                    continue
                survey = str(row["survey_type"]).strip()
                survey = {"facilitygroup": "Facility/Group", "dental": "Dental"}.get(token(survey), survey)
                task = str(row.get("task", "")).strip()
                explicit_campaign = row.get("campaign")
                explicit_channel = row.get("channel")
                channel = CHANNELS.get(token(task))
                if pd.notna(explicit_channel) and str(explicit_channel).strip():
                    channel = CHANNELS.get(token(explicit_channel), str(explicit_channel).strip())
                record = {field: number(row.get(field, np.nan)) for field in NUMERIC}
                for field in ("reported_outreach", "reported_response", "reported_bulk"):
                    source = row.get(field)
                    if pd.notna(source) and "%" in str(source):
                        record[field] /= 100
                record.update(
                    survey_type=survey,
                    start_date=date(row.get("start_date")),
                    end_date=date(row.get("end_date")),
                    source_sheet=sheet,
                    source_row=int(row_index) + 1,
                )
                if pd.notna(explicit_campaign):
                    campaign = str(explicit_campaign).strip()
                elif channel:
                    campaign = current
                elif token(task) == "campaignclose" or not task or task == "nan":
                    continue
                else:
                    campaign = task
                    current = task
                if not campaign:
                    issues.append(f"{sheet}, row {row_index + 1}: channel without a parent campaign skipped.")
                    continue
                record["campaign"] = campaign
                year = number(row.get("year", np.nan))
                if pd.isna(year):
                    year = record["start_date"].year if pd.notna(record["start_date"]) else np.nan
                if pd.isna(year):
                    match = re.search(r"(20\d{2})", campaign)
                    year = int(match.group(1)) if match else np.nan
                record["year"] = year
                for field in NUMERIC:
                    if pd.notna(record[field]) and record[field] < 0:
                        issues.append(f"{sheet}, row {row_index + 1}: negative {field} treated as missing.")
                        record[field] = np.nan
                if (
                    pd.isna(record["actual_outreach"])
                    and pd.notna(record["attempted_outreach"])
                    and pd.notna(record["outreach_fail"])
                ):
                    derived = record["attempted_outreach"] - record["outreach_fail"]
                    if derived >= 0:
                        record["actual_outreach"] = derived
                if channel:
                    record["channel"] = channel
                    activities.append(record)
                else:
                    summaries.append(record)
    if not summaries:
        raise UploadError(
            "No campaign summaries found. Include Survey type, Campaign name (or TASK), and count columns. Channel rows alone cannot establish unique campaign totals."
        )
    campaigns = pd.DataFrame(summaries)
    keys = ["year", "survey_type", "campaign"]
    duplicate = campaigns.duplicated(keys, keep=False)
    if duplicate.any():
        raise UploadError(
            "Duplicate campaign summaries found across sheets. Keep one summary per year, survey type, and campaign to avoid double counting."
        )
    channels = pd.DataFrame(activities, columns=[*campaigns.columns, "channel"])
    missing_year = campaigns.year.isna()
    if missing_year.any():
        issues.append(f"{missing_year.sum()} campaign(s) have no year; available under 'Unknown'.")
    from utils.portfolio_math import DEFINITIONS, ratio

    for _, row in campaigns.iterrows():
        if pd.notna(row.start_date) and pd.notna(row.end_date) and row.end_date < row.start_date:
            issues.append(f"{row.campaign}: end date precedes start date.")
        for (label, (num, den)), reported in zip(
            DEFINITIONS.items(), ["reported_outreach", "reported_response", "reported_bulk"]
        ):
            calculated = ratio(row[num], row[den])
            if pd.notna(calculated) and calculated > 100:
                issues.append(f"{row.campaign}: {label} exceeds 100%; review the counts.")
            if (
                pd.notna(calculated)
                and pd.notna(row[reported])
                and abs(calculated - row[reported] * 100) > 0.1
            ):
                issues.append(
                    f"{row.campaign}: stored {label.lower()} differs from the documented definition; calculated counts are used."
                )
    return Dataset(campaigns, channels, issues, accepted)

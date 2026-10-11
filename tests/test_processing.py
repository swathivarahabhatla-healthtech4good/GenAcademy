from pathlib import Path
import pandas as pd
import pytest
from utils.data_processing import load_upload, UploadError
from utils.portfolio_math import metrics, channel_mix


def parse(text):
    return load_upload(text.encode(), "campaigns.csv")


def test_summary_and_channels_are_not_double_counted():
    data = parse(
        "Survey type,Campaign name,Channel,Year,Target Outreach,Attempted Outreach,Actual Outreach,Actual responses,Bulk Close\nDental,Spring,,2025,100,90,80,40,20\nDental,Spring,Email Campaign,2025,,70,60,30,\nDental,Spring,Letter Campaign,2025,,20,20,10,\n"
    )
    assert len(data.campaigns) == 1
    assert len(data.channels) == 2
    assert metrics(data.campaigns)["Response rate"]["value"] == 50
    assert channel_mix(data.channels, "attempted_outreach").share_pct.sum() == pytest.approx(100)


def test_weighting_uses_matched_counts_and_preserves_missing():
    frame = pd.DataFrame(
        {
            "actual_outreach": [10, 90, 1000],
            "target_outreach": [20, 100, 2000],
            "responses": [10, 0, None],
            "bulk_close": [None, 0, None],
        }
    )
    value = metrics(frame)["Response rate"]
    assert value["value"] == 10
    assert value["coverage"] == 2
    assert metrics(frame)["Bulk closure rate"]["coverage"] == 0


def test_duplicate_summaries_rejected():
    with pytest.raises(UploadError, match="Duplicate"):
        parse("Survey type,Campaign name,Year,Actual responses\nDental,Spring,2025,5\nDental,Spring,2025,5\n")


def test_real_workbook():
    path = Path("GenAcademy_week1_Outreach.xlsx")
    if not path.exists():
        pytest.skip("User workbook unavailable")
    data = load_upload(path.read_bytes(), path.name)
    assert len(data.campaigns) == 7
    assert len(data.channels) > 20
    jan = data.campaigns[data.campaigns.campaign == "FAC&GRP_Jan2025"]
    assert metrics(jan)["Outreach rate"]["value"] == pytest.approx(9621 / 9827 * 100)
    assert metrics(jan)["Response rate"]["value"] == pytest.approx(5470 / 9621 * 100)
    assert any("stored response rate" in issue for issue in data.issues)


def test_bad_format_and_orphan_channels():
    with pytest.raises(UploadError):
        load_upload(b"garbage", "file.txt")
    with pytest.raises(UploadError, match="No campaign summaries"):
        parse("Survey type,TASK,Attempted Outreach\nDental,Email Campaign,10\n")


def test_missing_is_not_zero_and_failure_derivation():
    data = parse(
        "Survey type,Campaign name,Year,Attempted Outreach,Outreach fail,Actual responses,Bulk Close\nDental,Spring,2025,100,10,-,-\n"
    )
    assert data.campaigns.iloc[0].actual_outreach == 90
    assert pd.isna(metrics(data.campaigns)["Response rate"]["value"])


def test_ai_evidence_excludes_campaign_names_and_serializes_missing():
    import json
    from utils.llm_agent import evidence

    data = parse(
        "Survey type,Campaign name,Year,Attempted Outreach,Outreach fail,Actual responses,Bulk Close\nDental,Private Spring,2025,100,10,-,-\n"
    )
    payload = evidence(data.campaigns, data.channels, "Responses")
    assert "Private Spring" not in payload
    assert "NaN" not in payload
    assert json.loads(payload)["campaign_count"] == 1

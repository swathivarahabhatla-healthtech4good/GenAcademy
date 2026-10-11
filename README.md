# Campaign Advisor

Upload-driven Streamlit analysis of survey outreach calendars, with four consistent tabs: overview, outreach channels, response analysis, and bulk closure. Uses pandas, NumPy, Plotly, and Groq. No campaign values are entered manually and no sample metrics are injected.

## Run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then from this directory:

```powershell
uv sync
uv run streamlit run app.py
```

This workspace also has a project-local uv executable. If uv is not on PATH:

```powershell
$env:UV_CACHE_DIR = "$PWD\.tools\cache"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.tools\python"
.\.tools\uv.exe sync
.\.tools\uv.exe run streamlit run app.py
```

Open http://localhost:8501 and upload `GenAcademy_week1_Outreach.xlsx` using the app. It is never automatically loaded.

For this prepared Windows workspace, `./run.ps1` sets the project-local uv directories and launches the app.

The launcher also loads `.env` from the project root when present. Add `GROQ_API_KEY=your-key-here` there and restart using `./run.ps1`. For a direct uv launch with this file, use `uv run --env-file .env streamlit run app.py`. Existing environment variables take precedence; Streamlit secrets override the environment in this app.

For AI, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set your Groq key, or set `GROQ_API_KEY` in the environment. Optionally set `GROQ_MODEL`. Default: `llama-3.3-70b-versatile`. Click **Generate AI insights** in a detail tab. AI is optional; charts work without credentials. Never commit secrets.

## File contract

CSV, XLSX and XLS up to 20 MB. Excel may contain title rows and multiple campaign tables; unsupported definition/visual sheets are reported and skipped. Password-protected files are unsupported.

Supported headers (case and punctuation insensitive):

| Field | Headers |
| --- | --- |
| Survey | Survey type, SurveyType, Survey_Type |
| Campaign | Campaign name, Campaign, TASK |
| Channel | Channel, Outreach channel; channel TASK rows in the schedule format |
| Dates | Start, Start date, End, End date |
| Year | Year, Calendar year |
| Counts | Target Outreach, Attempted Outreach, Outreach fail, Actual Outreach, Actual responses, Bulk Close |
| Optional audit | Outreach Rate-KPI1, Response Rate-KPI2, Bulk Close Rate-KPI3, Cost |

One campaign summary per year/survey/campaign. Channel rows have the same Campaign name and a Channel value; their count columns describe that activity. In the supplied workbook, a campaign TASK establishes the parent for subsequent channel TASKs. Channel-only datasets are rejected because they cannot establish deduplicated campaign totals. Duplicate summaries are rejected to avoid inflating KPIs. An unknown channel should use an explicit Channel column.

The workbook's Project schedule is supported. Definition and 2024Visual sheets are excluded: 2024Visual contains Medical surveys and historical totals without unambiguous campaign identifiers/channel detail. To include those records, export them into the documented summary schema.

## Calculation rules

- Outreach rate = Actual Outreach / Target Outreach.
- Response rate = Actual responses / Actual Outreach.
- Bulk closure rate = Bulk Close / Actual responses.
- Aggregate rates sum matched numerator/denominator pairs, with positive denominators and coverage displayed. Missing and dash values remain unknown. Negative counts are excluded with notes. An absent actual outreach can be derived only when both attempted outreach and failure counts exist.
- Stored KPI values are audited against computed definitions. The provided workbook has inconsistent formulas; count-derived rates follow its Definition tab. Values above 100% are flagged and never silently capped.
- Channel pie shares normalize known attempts to 100%. These are contacts/efforts, not unique providers. Responses recorded on outreach rows do not prove inbound channel attribution. Mismatches against campaign totals are displayed.
- Calendar year uses an explicit year, then start date, then a year in the campaign name. Cross-year campaigns belong to their start year; counts are not split across years.
- Bulk Close represents recorded eligibility, not proof of completed closure. Costs are retained in exports; no external price or cost assumptions are applied.

`utils/portfolio_math.py` contains custom campaign arithmetic under the requested filename. yfinance is included as requested, but stock data has no role in survey analysis and is never fetched or mixed into upload-derived evidence.

## Privacy and deployment

Uploads and parsed data live in Streamlit session memory, without shared upload caches or disk persistence. Generated insights are session-local and keyed to selected aggregate evidence. Only aggregate counts and channel labels are submitted to Groq after a button click; raw provider rows and campaign names are excluded. The hosting process and Groq still process data: deploy behind your organization's authentication and HTTPS and use approved data handling policies. Authentication is a hosting responsibility, not implemented by this local app.

20 MB upload and 100 MB expanded XLSX limits bound common file sizes. Groq requests use timeouts and limited retries. Errors never expose API keys. No live Groq request is made by the tests.

## Validation

```powershell
uv run pytest -q
uv run ruff check .
```

Tests cover the supplied workbook, count weighting, missing values, duplicate rejection, channel normalization, and rendering/filter interactions in all four components. UI reference images have not been supplied; the app uses a consistent teal/navy layout ready for refinement.

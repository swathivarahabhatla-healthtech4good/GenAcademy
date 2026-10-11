"""Run with uv run streamlit run app.py."""

import hashlib
import streamlit as st
from utils.data_processing import load_upload, UploadError
from components import overview, outreach, responses, bulk_closure

st.set_page_config(page_title="Campaign Advisor", page_icon="📊", layout="wide")
st.markdown(
    """<style>
.block-container {padding-top:2rem; max-width:1550px}
h1 {font-size:2.3rem!important;letter-spacing:-.04em}
h2 {font-size:1.55rem!important;letter-spacing:-.02em}
h3 {font-size:1.1rem!important}
[data-testid="stMetricValue"] {font-size:2rem}
[data-testid="stTabs"] button {font-weight:600}
</style>""",
    unsafe_allow_html=True,
)
st.caption("SURVEY INTELLIGENCE / CAMPAIGN OPERATIONS")
st.title("Campaign Advisor")
st.write("Understand outreach. Find response patterns. Improve campaign efficiency.")
with st.container(border=True):
    uploaded = st.file_uploader(
        "Upload your outreach calendar summary",
        type=["csv", "xlsx", "xls"],
        help="Only uploaded file data is analyzed. All supported Excel sheets are inspected. Maximum 20 MB.",
    )
    st.caption("Multi-sheet Excel and CSV supported · No manual performance entry")
if uploaded is None:
    st.info("Upload your campaign summary to open the four analysis tabs.")
    with st.expander("Supported file structure and KPI definitions"):
        st.markdown("""Include **Survey type**, **Campaign name** (or **TASK**), **Start date** or **Year**, and your count columns: **Target Outreach**, **Attempted Outreach**, **Actual Outreach**, **Actual responses**, **Bulk Close**.

For channel detail, add separate rows with **Campaign name** and **Channel**. The provided Project schedule format is also supported: a campaign total TASK followed by its channel TASK rows. Summary and channel rows must remain separate.

Outreach rate = actual outreach / target outreach. Response rate = actual responses / actual outreach. Bulk closure rate = bulk close / actual responses. Missing counts remain unavailable. Aggregate KPIs use matched counts, not averages of percentages.""")
    st.stop()
content = uploaded.getvalue()
digest = hashlib.sha256(content + uploaded.name.encode()).hexdigest()
if st.session_state.get("upload_digest") != digest:
    try:
        dataset = load_upload(content, uploaded.name)
    except UploadError as exc:
        st.error(str(exc))
        st.stop()
    st.session_state["dataset"] = dataset
    st.session_state["upload_digest"] = digest
    st.session_state["analyses"] = {}
dataset = st.session_state["dataset"]
st.caption(
    f"SOURCE: {uploaded.name} · {len(dataset.campaigns)} campaigns · {len(dataset.channels)} channel activities · {len(dataset.sheets)} supported sheet(s)"
)
if dataset.issues:
    with st.expander(f"Data quality & import notes ({len(dataset.issues)})", expanded=False):
        for issue in dataset.issues:
            st.write(f"• {issue}")
with st.expander("Metric methodology"):
    st.write(
        "Outreach = actual outreach / target outreach; response = actual responses / actual outreach; bulk closure = bulk close / actual responses. Each aggregate uses only campaigns with both counts and a positive denominator. Coverage is shown on every KPI. Stored percentages are retained for auditing, but count-derived metrics take precedence. Year uses campaign start date, an explicit Year column, or a year in the campaign name. Channel activity is not added to campaign totals."
    )
tabs = st.tabs(["Overview", "Outreach channels", "Response analysis", "Bulk closure"])
for tab, component in zip(tabs, [overview, outreach, responses, bulk_closure]):
    with tab:
        component.render(dataset)
st.caption("Campaign Advisor · Upload-derived evidence · AI recommendations require human review")

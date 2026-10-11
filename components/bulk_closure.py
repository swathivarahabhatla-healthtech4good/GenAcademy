import streamlit as st
import plotly.express as px
from components.common import filters, chart, insights, rate_frame, fmt
from utils.portfolio_math import metrics


def render(dataset):
    left, right = st.columns([1, 3], gap="large")
    with left:
        frame, channels = filters(dataset, "bulk")
    with right:
        st.markdown("## Bulk Closure Rate")
        metric = metrics(frame)["Bulk closure rate"]
        st.metric("Bulk closure rate", fmt(metric["value"]))
        st.caption(
            f"Bulk eligible closures / actual responses · {metric['coverage']}/{metric['total']} campaigns with complete counts. Eligibility is not confirmation that closure was completed."
        )
        data = rate_frame(frame)
        if data["Bulk closure rate"].notna().any():
            chart(px.bar(data, x="campaign", y="Bulk closure rate", color="survey_type"), "bulk_chart")
        else:
            st.info("Bulk closure counts or response denominators are missing.")
        st.dataframe(
            frame[["campaign", "responses", "bulk_close", "reported_bulk"]],
            hide_index=True,
            use_container_width=True,
        )
        insights(
            frame,
            channels,
            "Bulk closure eligibility, data quality, and ways to reduce manual review",
            "bulk",
        )

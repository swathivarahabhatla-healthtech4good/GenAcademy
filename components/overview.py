import streamlit as st
import plotly.express as px
from components.common import filters, metric_cards, chart, rate_frame, COLORS


def render(dataset):
    left, right = st.columns([1, 3], gap="large")
    with left:
        frame, _ = filters(dataset, "overview", campaign=False)
    with right:
        st.markdown("## Performance overview")
        st.caption("Weighted campaign metrics · count-based and traceable")
        metric_cards(frame)
        data = rate_frame(frame)
        if not data.empty:
            melted = data.melt(
                id_vars=["campaign"],
                value_vars=["Outreach rate", "Response rate", "Bulk closure rate"],
                var_name="KPI",
                value_name="Rate (%)",
            )
            chart(
                px.bar(
                    melted,
                    x="campaign",
                    y="Rate (%)",
                    color="KPI",
                    barmode="group",
                    color_discrete_sequence=COLORS,
                ),
                "overview_chart",
            )
        st.markdown("### Campaign performance")
        st.dataframe(data, hide_index=True, use_container_width=True)
        st.download_button(
            "Export selected campaign counts",
            frame.to_csv(index=False),
            "campaign-performance.csv",
            "text/csv",
            key="export_overview",
        )

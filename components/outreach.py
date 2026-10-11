import streamlit as st
import plotly.express as px
from components.common import filters, chart, insights, COLORS
from utils.portfolio_math import channel_mix


def render(dataset):
    left, right = st.columns([1, 3], gap="large")
    with left:
        frame, channels = filters(dataset, "outreach")
    with right:
        st.markdown("## Outreach channel details")
        st.caption("Email campaign · Custom emails · Call Logic support · Letter campaign")
        mix = channel_mix(channels, "attempted_outreach")
        if mix.empty or mix.attempted_outreach.sum() <= 0:
            st.info("No positive channel attempt counts are available for this selection.")
        else:
            chart(
                px.pie(
                    mix,
                    names="channel",
                    values="attempted_outreach",
                    hole=0.6,
                    color_discrete_sequence=COLORS,
                ),
                "outreach_pie",
            )
            st.dataframe(mix, hide_index=True, use_container_width=True)
        st.caption(
            "Shares total 100% of known recorded channel attempts. This is effort distribution, not unique provider coverage; providers may receive multiple contacts. Missing channel counts are excluded."
        )
        st.dataframe(
            channels[
                [
                    "campaign",
                    "channel",
                    "start_date",
                    "end_date",
                    "attempted_outreach",
                    "outreach_fail",
                    "actual_outreach",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )
        insights(
            frame, channels, "Outreach channel effort and opportunities to reduce failed contacts", "outreach"
        )

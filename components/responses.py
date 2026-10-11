import streamlit as st
import plotly.express as px
from components.common import filters, chart, insights, COLORS
from utils.portfolio_math import channel_mix


def render(dataset):
    left, right = st.columns([1, 3], gap="large")
    with left:
        frame, channels = filters(dataset, "responses")
    with right:
        st.markdown("## Response details")
        mix = channel_mix(channels, "responses")
        if mix.empty:
            st.info("Response channel attribution is missing in the uploaded data.")
        else:
            chart(
                px.bar(mix, x="channel", y="responses", color="channel", color_discrete_sequence=COLORS),
                "response_bar",
            )
            st.dataframe(mix, hide_index=True, use_container_width=True)
        st.caption(
            "Responses are attributed to the outreach activity recorded in the workbook. This does not establish the actual inbound channel or deduplicated responses."
        )
        valid = frame.responses.notna()
        if valid.any():
            total = frame.loc[valid, "responses"].sum()
            st.metric("Recorded campaign responses", f"{total:,.0f}")
            channel_total = channels.responses.sum(min_count=1)
            if channel_total == channel_total and abs(channel_total - total) > 0.5:
                st.warning(
                    f"Channel response total ({channel_total:,.0f}) differs from campaign responses ({total:,.0f}). Review overlap, missing channels, and attribution before interpreting channel shares."
                )
        insights(
            frame,
            channels,
            "Response patterns, channel attribution limitations, and practical follow-up experiments",
            "responses",
        )

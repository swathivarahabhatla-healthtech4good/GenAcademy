import hashlib
import os
import numpy as np
import pandas as pd
import streamlit as st
from utils.llm_agent import analyze, evidence
from utils.portfolio_math import metrics, DEFINITIONS

COLORS = ["#16A394", "#4361EE", "#F4B860", "#A77DE0", "#EC799A", "#75BDE0"]


def fmt(value):
    return "Unavailable" if pd.isna(value) else f"{value:,.1f}%"


def filters(dataset, key, campaign=True):
    frame = dataset.campaigns
    with st.container(border=True):
        st.markdown("### Filter campaigns")
        years = sorted(frame.year.dropna().astype(int).unique().tolist())
        options = ["All years", *years]
        if frame.year.isna().any():
            options.append("Unknown")
        year = st.selectbox("Calendar year", options, key=f"{key}_year")
        if year == "Unknown":
            frame = frame[frame.year.isna()]
        elif year != "All years":
            frame = frame[frame.year == year]
        survey = st.selectbox(
            "Survey type", ["All survey types", *sorted(frame.survey_type.unique())], key=f"{key}_survey"
        )
        if survey != "All survey types":
            frame = frame[frame.survey_type == survey]
        if campaign:
            selected = st.selectbox(
                "Campaign name", ["All campaigns", *sorted(frame.campaign.unique())], key=f"{key}_campaign"
            )
            if selected != "All campaigns":
                frame = frame[frame.campaign == selected]
        st.caption(f"{len(frame)} campaign(s) in this view")
    keys = ["year", "survey_type", "campaign"]
    channels = dataset.channels.merge(frame[keys], on=keys, how="inner")
    return frame, channels


def metric_cards(frame):
    for column, (label, metric) in zip(st.columns(3), metrics(frame).items()):
        with column:
            with st.container(border=True):
                st.metric(label, fmt(metric["value"]))
                st.caption(
                    f"{metric['numerator']:,.0f} / {metric['denominator']:,.0f} · {metric['coverage']}/{metric['total']} campaigns with complete counts"
                )


def chart(fig, key):
    fig.update_layout(
        font=dict(family="Arial", color="#172B4D"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=35, b=10),
        colorway=COLORS,
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def insights(frame, channels, focus, key):
    st.markdown("### Campaign advisor")
    if frame.empty:
        st.info("No campaigns match these filters.")
        return
    rates = frame.dropna(subset=["responses", "actual_outreach"]).copy()
    rates = rates[rates.actual_outreach > 0]
    if not rates.empty:
        rates["rate"] = rates.responses / rates.actual_outreach * 100
        best = rates.loc[rates.rate.idxmax()]
        st.info(
            f"Highest recorded response rate in this selection: {best.campaign} ({best.rate:.1f}%). Channel overlap and campaign differences limit comparisons."
        )
    st.caption(
        "Groq receives aggregate KPIs and channel totals only when you request analysis. No raw rows or campaign names are sent."
    )
    payload = evidence(frame, channels, focus)
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    api_key = os.getenv("GROQ_API_KEY", "")
    try:
        api_key = st.secrets.get("GROQ_API_KEY", api_key)
        model = st.secrets.get("GROQ_MODEL", model)
    except st.errors.StreamlitSecretNotFoundError:
        pass
    digest = hashlib.sha256((payload + model).encode()).hexdigest()
    cache = st.session_state.setdefault("analyses", {})
    if st.button("Generate AI insights", key=f"{key}_ai", disabled=not api_key):
        try:
            with st.spinner("Analyzing the selected campaign evidence…"):
                cache[digest] = analyze(payload, api_key, model)
        except Exception:
            st.error(
                "Groq analysis is unavailable. Check your API key, model access, network, or quota and retry."
            )
    if not api_key:
        st.caption("Set GROQ_API_KEY in environment variables or .streamlit/secrets.toml to enable AI.")
    if digest in cache:
        st.markdown(cache[digest])
        st.download_button("Download insights", cache[digest], f"{key}-insights.md", key=f"{key}_download")


def rate_frame(frame):
    data = frame[["campaign", "start_date", "year", "survey_type"]].copy()
    for label, (num, den) in DEFINITIONS.items():
        data[label] = np.where(frame[den] > 0, frame[num] / frame[den] * 100, np.nan)
    return data

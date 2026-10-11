"""Campaign KPI arithmetic; historical filename retained as requested."""

import numpy as np
import pandas as pd

DEFINITIONS = {
    "Outreach rate": ("actual_outreach", "target_outreach"),
    "Response rate": ("responses", "actual_outreach"),
    "Bulk closure rate": ("bulk_close", "responses"),
}


def ratio(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator <= 0:
        return np.nan
    return float(numerator) / float(denominator) * 100


def metrics(frame):
    """Use matched valid pairs, never turn missing values into zeros."""
    result = {}
    for label, (num, den) in DEFINITIONS.items():
        valid = frame[num].notna() & frame[den].notna() & (frame[den] > 0)
        pairs = frame.loc[valid]
        result[label] = {
            "value": ratio(pairs[num].sum(), pairs[den].sum()),
            "numerator": float(pairs[num].sum()),
            "denominator": float(pairs[den].sum()),
            "coverage": int(valid.sum()),
            "total": len(frame),
        }
    return result


def channel_mix(channels, column):
    known = channels.dropna(subset=[column])
    grouped = known.groupby("channel", as_index=False)[column].sum()
    total = grouped[column].sum()
    grouped["share_pct"] = grouped[column] / total * 100 if total > 0 else np.nan
    return grouped.sort_values(column, ascending=False)

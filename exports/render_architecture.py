"""Render a shareable architecture diagram using vector shapes and Pillow."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1800, 1450
img = Image.new("RGB", (W, H), "#F5F7FB")
draw = ImageDraw.Draw(img)
font_path = Path("C:/Windows/Fonts/arial.ttf")
bold_path = Path("C:/Windows/Fonts/arialbd.ttf")


def font(size, bold=False):
    return ImageFont.truetype(str(bold_path if bold else font_path), size)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="100%" height="100%" fill="#F5F7FB"/>',
       '<defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10" fill="none" stroke="#667892" stroke-width="2"/></marker></defs>']


def label(x, y, text, size=25, bold=False, color="#172B4D"):
    draw.text((x, y), text, font=font(size, bold), fill=color, anchor="mm")
    svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(text)}</text>')


def box(x, y, w, h, title, subtitle, fill="#FFFFFF", stroke="#CCD6E4"):
    draw.rounded_rectangle((x, y, x+w, y+h), radius=18, fill=fill, outline=stroke, width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    label(x+w/2, y+38, title, 28, True)
    for i, line in enumerate(subtitle.split("\n")):
        label(x+w/2, y+76+i*30, line, 23, color="#526580")


def arrow(points):
    draw.line(points, fill="#667892", width=3)
    x, y = points[-1]
    px, py = points[-2]
    if y > py:
        triangle = [(x, y), (x-7, y-13), (x+7, y-13)]
    elif x > px:
        triangle = [(x, y), (x-13, y-7), (x-13, y+7)]
    else:
        triangle = [(x, y), (x+13, y-7), (x+13, y+7)]
    draw.polygon(triangle, fill="#667892")
    coords = " ".join(f"{x},{y}" for x, y in points)
    svg.append(f'<polyline points="{coords}" fill="none" stroke="#667892" stroke-width="3" marker-end="url(#arrow)"/>')


label(900, 65, "Campaign Advisor | Application Architecture", 43, True)
label(900, 115, "Upload-driven survey analytics with optional Groq insights", 27, color="#526580")

box(70, 180, 470, 125, "CSV / Excel upload", "Campaign summaries + channel rows")
box(665, 180, 470, 125, "Streamlit application", "app.py | Browser: localhost:8501", fill="#E4F4F1", stroke="#16A394")
box(1260, 180, 470, 125, "Launch + configuration", "run.ps1 + uv | Project .env")
arrow([(540, 242), (665, 242)])
arrow([(1260, 242), (1135, 242)])

box(665, 360, 470, 150, "Read and validate", "data_processing.py\nNormalize headers; separate row types")
arrow([(900, 305), (900, 360)])
box(665, 565, 470, 150, "Session memory", "Campaign totals + channel activity\nImport notes; no upload database")
arrow([(900, 510), (900, 565)])
box(665, 770, 470, 125, "Filter selected data", "Year | Survey type | Campaign")
arrow([(900, 715), (900, 770)])

box(70, 950, 710, 145, "Calculate metrics in Python", "portfolio_math.py | pandas + NumPy\nWeighted KPIs; channel effort shares", fill="#E4F4F1", stroke="#16A394")
box(1030, 950, 700, 145, "Prepare AI evidence", "llm_agent.py | Aggregates + anonymized campaigns\nSent only after Generate AI insights is clicked", fill="#EBEDFF", stroke="#4361EE")
arrow([(800, 895), (800, 920), (425, 920), (425, 950)])
arrow([(1000, 895), (1000, 920), (1380, 920), (1380, 950)])

box(70, 1150, 710, 145, "Four consistent Streamlit tabs", "Overview | Outreach | Responses | Bulk closure\nPlotly charts, tables, CSV and insight downloads")
box(1030, 1150, 700, 145, "Groq API -> AI recommendations", "Observations, patterns and practical actions\nResults returned to the app and kept in session")
arrow([(425, 1095), (425, 1150)])
arrow([(1380, 1095), (1380, 1150)])
arrow([(1030, 1222), (780, 1222)])

label(900, 1355, "Python computes the numbers. Groq interprets the evidence.", 29, True)
label(900, 1400, "No raw provider rows or campaign names sent to Groq. yfinance is installed but unused.", 23, color="#526580")
svg.append("</svg>")
img.save(ROOT / "campaign-architecture.png", dpi=(180, 180))
(ROOT / "campaign-architecture.svg").write_text("\n".join(svg), encoding="utf-8")
print("Exported campaign-architecture.png and campaign-architecture.svg")

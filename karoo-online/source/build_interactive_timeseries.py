"""Interactive 4-year revenue time-series with a time-frame selector
(1Y / 2Y / 4Y buttons + range slider) and the oil price overlaid, so users
can explore any window. Outputs an embeddable HTML fragment."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

OUT = Path(__file__).parent / "out"
df = pd.read_csv(OUT / "timeseries_4yr.csv")
df["date"] = pd.to_datetime(df["month"] + "-01")

fig = go.Figure()
# Revenue bars
fig.add_trace(go.Bar(
    x=df["date"], y=df["revenue_m"], name="Revenue (Rm)",
    marker_color="#C0531F", opacity=0.85,
    hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: R%{y:.1f}m<extra></extra>"))
# Orders line (secondary)
fig.add_trace(go.Scatter(
    x=df["date"], y=df["orders"] / 1000, name="Orders (000s)", yaxis="y2",
    mode="lines", line=dict(color="#2A7F7F", width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>Orders: %{y:.0f}k<extra></extra>"))
# Brent oil line (secondary)
fig.add_trace(go.Scatter(
    x=df["date"], y=df["brent_usd"], name="Brent ($/bbl)", yaxis="y2",
    mode="lines", line=dict(color="#2B2118", width=1.6, dash="dot"),
    hovertemplate="<b>%{x|%b %Y}</b><br>Brent: $%{y}<extra></extra>"))

# annotate the 2026 oil crisis
fig.add_vrect(x0="2026-02-01", x1="2026-06-01", fillcolor="#A5361A", opacity=0.08,
              line_width=0, annotation_text="2026 oil crisis", annotation_position="top left",
              annotation_font_size=10, annotation_font_color="#A5361A")

fig.update_layout(
    height=470, margin=dict(l=0, r=0, t=8, b=0),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI", color="#2B2118"),
    legend=dict(orientation="h", y=1.12, x=0),
    yaxis=dict(title="Revenue (R millions)", gridcolor="#eee"),
    yaxis2=dict(title="Orders (000s) · Brent ($)", overlaying="y", side="right", showgrid=False),
    xaxis=dict(
        rangeselector=dict(buttons=[
            dict(count=1, label="1Y", step="year", stepmode="backward"),
            dict(count=2, label="2Y", step="year", stepmode="backward"),
            dict(count=3, label="3Y", step="year", stepmode="backward"),
            dict(step="all", label="4Y / All"),
        ], bgcolor="#FBF3EC", activecolor="#C0531F", font=dict(color="#2B2118")),
        rangeslider=dict(visible=True, thickness=0.08),
        type="date"),
    barmode="overlay", dragmode="pan")

html = fig.to_html(full_html=False, include_plotlyjs="cdn", config={
    "displayModeBar": True, "scrollZoom": True, "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"]})
(OUT / "interactive_timeseries_fragment.html").write_text(html, encoding="utf-8")
print("Interactive time-series (4Y, selectable) written.")

# static PNG for the PDF edition
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig2, ax = plt.subplots(figsize=(11, 4.6))
ax.bar(df["date"], df["revenue_m"], width=22, color="#C0531F", alpha=0.85)
ax2 = ax.twinx()
ax2.plot(df["date"], df["brent_usd"], color="#2B2118", lw=1.4, ls=":", label="Brent $/bbl")
ax.axvspan(pd.Timestamp("2026-02-01"), pd.Timestamp("2026-06-01"), color="#A5361A", alpha=0.08)
ax.set_ylabel("Revenue (R millions)", color="#C0531F"); ax2.set_ylabel("Brent $/bbl", color="#2B2118")
ax.set_title("Revenue Over Four Years (Jul 2022 – Jun 2026)", fontweight="bold", color="#2B2118")
ax.spines[["top"]].set_visible(False); ax2.spines[["top"]].set_visible(False)
fig2.tight_layout(); fig2.savefig(OUT / "charts" / "ts_4yr.png", dpi=150, bbox_inches="tight", facecolor="white")
print("static ts_4yr.png written")

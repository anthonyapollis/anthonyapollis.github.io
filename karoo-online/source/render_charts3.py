"""Charts for customer lifecycle/churn/CLV and the oil-trade impact."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "out"
CHARTS = OUT / "charts"
K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0", "cream": "#FBF3EC",
     "teal": "#2A7F7F", "sage": "#6B8E5A", "gold": "#E0A526", "coral": "#E07856", "sky": "#4A90C2",
     "plum": "#7D5BA6", "rust": "#A5361A", "green": "#4C7A4C", "berry": "#9C3B5A"}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": K["ink"],
                     "font.size": 11, "text.color": K["ink"], "axes.labelcolor": K["clay"],
                     "xtick.color": K["clay"], "ytick.color": K["clay"]})


def save(fig, n):
    fig.savefig(CHARTS / n, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ══ LIFECYCLE ══
stages = pd.read_csv(OUT / "lifecycle_stages.csv")
clv = pd.read_csv(OUT / "clv_bands.csv")
cohort = pd.read_csv(OUT / "cohort_retention.csv")

# 1. Lifecycle stages (funnel-style)
sc = {"New": K["sky"], "Active": K["green"], "At Risk": K["gold"], "Dormant": K["coral"], "Churned": K["rust"]}
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(stages["lifecycle_stage"], stages["customers"]/1000,
              color=[sc[s] for s in stages["lifecycle_stage"]], edgecolor="white", width=0.7)
for b, c, r in zip(bars, stages["customers"], stages["revenue"]):
    ax.text(b.get_x()+b.get_width()/2, c/1000+0.8, f"{c/1000:.1f}k\nR{r/1e6:.0f}m", ha="center", fontsize=9)
ax.set_title("Customer Lifecycle Stages — from New to Churned")
ax.set_ylabel("Customers (thousands)")
ax.set_ylim(0, stages["customers"].max()/1000*1.2)
save(fig, "lifecycle_stages.png")

# 2. CLV distribution
fig, ax = plt.subplots(figsize=(9, 4.8))
colors = [K["sand"], K["gold"], K["coral"], K["ochre"], K["rust"]]
bars = ax.bar(clv["clv_band"].astype(str), clv["customers"]/1000, color=colors, edgecolor="white")
ax2 = ax.twinx()
ax2.plot(range(len(clv)), clv["total_clv"]/1e9, "o-", color=K["ink"], lw=2, ms=8, label="Total CLV (Rbn)")
ax2.set_ylabel("Total CLV in band (R bn)")
for b, c in zip(bars, clv["customers"]):
    ax.text(b.get_x()+b.get_width()/2, c/1000+0.5, f"{c/1000:.0f}k", ha="center", fontsize=9)
ax.set_title("Customer Lifetime Value — Distribution & Concentration")
ax.set_ylabel("Customers (thousands)"); ax.set_xlabel("CLV band")
ax2.legend(loc="upper right")
save(fig, "clv_bands.png")

# 3. Cohort retention heatmap
piv = cohort.pivot(index="cohort", columns="month_offset", values="retention_pct")
fig, ax = plt.subplots(figsize=(11, 6.5))
im = ax.imshow(piv.values, cmap="YlOrBr_r", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns)
ax.set_yticks(range(len(piv))); ax.set_yticklabels(piv.index, fontsize=7)
ax.set_xlabel("Months since first purchase"); ax.set_title("Cohort Retention — % still active")
for i in range(len(piv)):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                    color="white" if v < 45 else K["ink"])
fig.colorbar(im, ax=ax, shrink=0.7, label="% retained")
save(fig, "cohort_retention.png")

# ══ OIL IMPACT ══
oil = pd.read_csv(OUT / "oil_impact_monthly.csv")
oilcat = pd.read_csv(OUT / "oil_impact_categories.csv")

# 4. Oil price + delivery cost dual axis
fig, ax = plt.subplots(figsize=(11, 5))
x = range(len(oil))
ax.fill_between(x, oil["brent_usd"], color=K["ink"], alpha=0.12)
ax.plot(x, oil["brent_usd"], color=K["ink"], lw=2.5, label="Brent crude (US$/bbl)")
ax2 = ax.twinx()
ax2.plot(x, oil["delivery_cost_per_order"], color=K["ochre"], lw=2.5, ls="--",
         label="Delivery cost/order (R)")
ax.set_xticks(list(x)[::2]); ax.set_xticklabels(oil["month"][::2], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Brent US$/bbl", color=K["ink"]); ax2.set_ylabel("Delivery cost/order (R)", color=K["ochre"])
peak_i = oil["oil_shock_pct"].idxmax()
ax.annotate("2026 Strait of Hormuz crisis\nBrent peaks ~$120 (Mar 2026)\nlargest shock since the 1970s",
            (peak_i, oil["brent_usd"].iloc[peak_i]),
            xytext=(max(peak_i-8, 0.3), oil["brent_usd"].max()-2), fontsize=8.5, color=K["rust"],
            fontweight="bold", arrowprops=dict(arrowstyle="->", color=K["rust"]))
ax.set_title("2026 Oil Shock — Brent Crude vs Karoo Online Delivery Cost")
ax.legend(loc="upper left", fontsize=8); ax2.legend(loc="upper right", fontsize=8)
ax.set_xlim(0, len(oil)-1)
save(fig, "oil_delivery.png")

# 5. Revenue actual vs baseline (the lost-revenue gap)
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(x, oil["revenue_baseline"]/1e6, color=K["sage"], lw=2, ls="--", label="Expected (no shock)")
ax.plot(x, oil["revenue"]/1e6, color=K["ochre"], lw=2.5, label="Actual (with oil shock)")
ax.fill_between(x, oil["revenue"]/1e6, oil["revenue_baseline"]/1e6,
                where=(oil["revenue"] < oil["revenue_baseline"]), color=K["rust"], alpha=0.25, label="Revenue lost")
ax.set_xticks(list(x)[::2]); ax.set_xticklabels(oil["month"][::2], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Monthly revenue (R millions)")
ax.set_title("Revenue Impact — Actual vs Shock-Free Baseline")
ax.legend(loc="lower right", fontsize=9); ax.set_xlim(0, len(oil)-1)
save(fig, "oil_revenue.png")

# 6. Category demand drop at peak
oc = oilcat.sort_values("peak_demand_drop_pct")
fig, ax = plt.subplots(figsize=(9.5, 5))
colors = [K["rust"] if t == "Discretionary" else K["sage"] for t in oc["type"]]
bars = ax.barh(oc["category"], oc["peak_demand_drop_pct"], color=colors, edgecolor="white")
for b, v in zip(bars, oc["peak_demand_drop_pct"]):
    ax.text(v+0.1, b.get_y()+b.get_height()/2, f"-{v:.1f}%", va="center", fontsize=9, fontweight="bold")
ax.set_title("Peak Demand Impact by Category (oil shock)")
ax.set_xlabel("Demand drop at peak (%)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=K["rust"], label="Discretionary (hit hard)"),
                   Patch(color=K["sage"], label="Essential (resilient)")], loc="lower right")
save(fig, "oil_categories.png")

print("Lifecycle + oil charts rendered.")

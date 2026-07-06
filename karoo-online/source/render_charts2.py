"""Render charts for the product catalogue analysis + the behavioural
analyses (correlations, recommendations, fraud) — Karoo Online story."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize

HERE = Path(__file__).parent
OUT = HERE / "out"
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0",
     "cream": "#FBF3EC", "teal": "#2A7F7F", "sage": "#6B8E5A", "gold": "#E0A526",
     "coral": "#E07856", "plum": "#7D5BA6", "sky": "#4A90C2", "rust": "#A5361A",
     "olive": "#8A8B4C", "berry": "#9C3B5A", "green": "#4C7A4C"}
CAT12 = [K["ochre"], K["teal"], K["gold"], K["sage"], K["plum"], K["coral"],
         K["sky"], K["rust"], K["olive"], K["berry"], K["clay"], "#3E8E7E"]
SEQ = LinearSegmentedColormap.from_list("k", ["#FBEFE2", "#E0A526", "#C0531F", "#7A2E12"])
DIVERGE = LinearSegmentedColormap.from_list("d", ["#2A7F7F", "#FBF3EC", "#C0531F"])
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 14, "axes.titleweight": "bold",
                     "axes.titlecolor": K["ink"], "font.size": 11, "text.color": K["ink"],
                     "axes.labelcolor": K["clay"], "xtick.color": K["clay"], "ytick.color": K["clay"]})


def savefig(fig, name):
    fig.savefig(CHARTS / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ═══ CATALOGUE: products ═══
tk = pd.read_csv(OUT / "takealot_products_clean.csv")
tk_cat = pd.read_csv(OUT / "tk_category_summary.csv")
tk_avail = pd.read_csv(OUT / "tk_availability.csv")
tk_top = pd.read_csv(OUT / "tk_top10_price.csv")

# 1. Price distribution (log)
fig, ax = plt.subplots(figsize=(10, 4.8))
priced = tk[tk["price"] > 0]
ax.hist(priced["price"], bins=np.logspace(np.log10(25), np.log10(55000), 45),
        color=K["ochre"], edgecolor="white", alpha=0.9)
ax.set_xscale("log")
med = priced["price"].median()
ax.axvline(med, color=K["teal"], ls="--", lw=2, label=f"median R{med:.0f}")
ax.set_title("Product Catalogue — Price Distribution (1,000 products)")
ax.set_xlabel("Price (R, log scale)"); ax.set_ylabel("Products")
ax.legend()
savefig(fig, "tk_price_dist.png")

# 2. Category breakdown (real)
cs = tk_cat.sort_values("products")
fig, ax = plt.subplots(figsize=(9.5, 5.5))
colors = [CAT12[i % len(CAT12)] for i in range(len(cs))]
bars = ax.barh(cs["category"], cs["products"], color=colors, edgecolor="white")
for b, n, mp in zip(bars, cs["products"], cs["median_price"]):
    ax.text(n + 3, b.get_y()+b.get_height()/2, f"{n}  ·  median R{mp:.0f}", va="center", fontsize=8.5)
ax.set_title("Real Product Mix by Category (classified from titles)")
ax.set_xlabel("Number of products")
ax.set_xlim(0, cs["products"].max()*1.25)
savefig(fig, "tk_categories.png")

# 3. Availability donut
fig, ax = plt.subplots(figsize=(7, 5.5))
acolors = {"In stock (fast)": K["green"], "Lead time (imported)": K["gold"],
           "No live offer": K["rust"], "Other": K["sand"]}
av = tk_avail.set_index("availability_bucket")
ax.pie(av["products"], labels=av.index, autopct=lambda p: f"{p:.0f}%",
       colors=[acolors.get(i, K["clay"]) for i in av.index],
       wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
       textprops={"fontsize": 10})
ax.set_title("Availability — the Fulfilment Reality", pad=16)
savefig(fig, "tk_availability.png")

# 4. Top 10 most expensive real products
tt = tk_top.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 5.5))
labels = [t[:42] + ("…" if len(t) > 42 else "") for t in tt["title"]]
norm = Normalize(tt["price"].min(), tt["price"].max())
bars = ax.barh(labels, tt["price"], color=SEQ(norm(tt["price"])), edgecolor="white")
for b, p in zip(bars, tt["price"]):
    ax.text(p + 400, b.get_y()+b.get_height()/2, f"R{p:,.0f}", va="center", fontsize=8.5, fontweight="bold")
ax.set_title("Top 10 Most Expensive Real Products")
ax.set_xlabel("Price (R)")
ax.set_xlim(0, tt["price"].max()*1.2)
ax.tick_params(labelsize=8)
savefig(fig, "tk_top_price.png")

# ═══ BEHAVIOURAL: correlations, recommendations, fraud ═══
corr = pd.read_csv(OUT / "rb_correlation_matrix.csv", index_col=0)
rec = pd.read_csv(OUT / "rb_recommendations.csv")
fraud = pd.read_csv(OUT / "rb_fraud_summary.csv")

# 5. Correlation heatmap
fig, ax = plt.subplots(figsize=(8.5, 7))
im = ax.imshow(corr.values, cmap=DIVERGE, vmin=-1, vmax=1)
ax.set_xticks(range(len(corr.columns))); ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
ax.set_yticks(range(len(corr.index))); ax.set_yticklabels(corr.index, fontsize=9)
for i in range(len(corr.index)):
    for j in range(len(corr.columns)):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if abs(v) > 0.55 else K["ink"], fontsize=8)
ax.set_title("Correlation Matrix — what drives what", pad=12)
fig.colorbar(im, ax=ax, shrink=0.7, label="Pearson r")
savefig(fig, "rb_correlation.png")

# 6. Recommendations — top pairs by lift (diverging from 1.0)
rt = rec.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 5.5))
labels = [f"{a}  +  {b}" for a, b in zip(rt["antecedent"], rt["consequent"])]
colors = [K["teal"] if l >= 1.2 else K["gold"] if l >= 1.1 else K["sand"] for l in rt["lift"]]
bars = ax.barh(labels, rt["lift"], color=colors, edgecolor="white")
ax.axvline(1.0, color=K["clay"], ls="--", lw=1.5, label="no association (lift=1)")
for b, l, c in zip(bars, rt["lift"], rt["confidence"]):
    ax.text(l + 0.005, b.get_y()+b.get_height()/2, f"{l:.2f}×  ({c*100:.0f}% conf)", va="center", fontsize=8.5)
ax.set_title("Product Recommendations — Category Affinities (by lift)")
ax.set_xlabel("Lift (higher = stronger 'bought together')")
ax.set_xlim(0.95, rt["lift"].max()*1.12)
ax.legend(loc="lower right", fontsize=8)
savefig(fig, "rb_recommendations.png")

# 7. Fraud — flagged vs real fraud captured
fig, ax = plt.subplots(figsize=(10, 5))
y = np.arange(len(fraud))
ax.barh(y + 0.2, fraud["flagged"], height=0.4, color=K["sand"], label="Total flagged", edgecolor=K["clay"])
ax.barh(y - 0.2, fraud["captures_real_fraud"], height=0.4, color=K["rust"], label="Real fraud caught")
ax.set_yticks(y); ax.set_yticklabels(fraud["signal"], fontsize=9)
for i, (f, c) in enumerate(zip(fraud["flagged"], fraud["captures_real_fraud"])):
    prec = c / f * 100 if f else 0
    ax.text(max(f, c) + 40, i, f"{prec:.0f}% precision", va="center", fontsize=8, color=K["ink"])
ax.set_title("Fraud Detection — Flagged vs Real Fraud Caught")
ax.set_xlabel("Customers")
ax.legend(loc="lower right")
ax.set_xlim(0, fraud["flagged"].max()*1.3)
savefig(fig, "rb_fraud.png")

print("Rendered catalogue + behavioural charts to", CHARTS)

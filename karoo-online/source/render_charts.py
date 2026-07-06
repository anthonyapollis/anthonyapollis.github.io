"""Render the full colourful chart set for the Karoo data story, including
a real South-African province choropleth (districts dissolved to provinces)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).parent
OUT = HERE / "out"
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

# ── Karoo palette: warm base + richer accent colours ──
K = {
    "ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0",
    "cream": "#FBF3EC", "teal": "#2A7F7F", "sage": "#6B8E5A", "gold": "#E0A526",
    "coral": "#E07856", "plum": "#7D5BA6", "sky": "#4A90C2", "rust": "#A5361A",
    "olive": "#8A8B4C", "berry": "#9C3B5A",
}
# 12-colour categorical spread for categories/brands
CAT12 = [K["ochre"], K["teal"], K["gold"], K["sage"], K["plum"], K["coral"],
         K["sky"], K["rust"], K["olive"], K["berry"], K["clay"], "#3E8E7E"]
KAROO_SEQ = LinearSegmentedColormap.from_list("karoo", ["#FBEFE2", "#E0A526", "#C0531F", "#7A2E12"])

plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": K["ink"],
    "font.size": 11, "axes.edgecolor": "#B8A48F", "text.color": K["ink"],
    "axes.labelcolor": K["clay"], "xtick.color": K["clay"], "ytick.color": K["clay"],
    "figure.facecolor": "white",
})

products = pd.read_csv(OUT / "products_master.csv")
brands = pd.read_csv(OUT / "brands.csv")
cats = pd.read_csv(OUT / "category_summary.csv")
prov_cat = pd.read_csv(OUT / "province_category.csv")
monthly_cat = pd.read_csv(OUT / "monthly_category.csv")


def savefig(fig, name):
    fig.savefig(CHARTS / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def money(x):
    return f"R{x/1e6:.0f}m" if x < 1e9 else f"R{x/1e9:.2f}bn"


# ═══════════════════════════════════════════════════════════════
# 1. TOP 10 BEST PRODUCTS (horizontal, gradient bars + rating dots)
# ═══════════════════════════════════════════════════════════════
top = products.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(9.5, 5.5))
norm = Normalize(top["revenue"].min(), top["revenue"].max())
colors = KAROO_SEQ(norm(top["revenue"]))
bars = ax.barh([f"{n}\n{b}" for n, b in zip(top["product_name"], top["brand"])],
               top["revenue"] / 1e6, color=colors, edgecolor="white", linewidth=0.8)
for b, r, rt in zip(bars, top["revenue"], top["avg_rating"]):
    ax.text(r/1e6 + 6, b.get_y()+b.get_height()/2, f"{money(r)}  ★{rt}",
            va="center", fontsize=9, color=K["ink"], fontweight="bold")
ax.set_title("Top 10 Products by Revenue", pad=14)
ax.set_xlabel("Revenue (R millions)")
ax.set_xlim(0, top["revenue"].max()/1e6 * 1.25)
ax.tick_params(labelsize=8.5)
savefig(fig, "top10_products.png")

# ═══════════════════════════════════════════════════════════════
# 2. WORST 10 PRODUCTS (muted, with rating + return context)
# ═══════════════════════════════════════════════════════════════
worst = products.tail(10)
fig, ax = plt.subplots(figsize=(9.5, 5.5))
bars = ax.barh([f"{n}\n{b}" for n, b in zip(worst["product_name"], worst["brand"])],
               worst["revenue"] / 1e6, color=K["sand"], edgecolor=K["clay"], linewidth=1)
for b, r, rt, rp in zip(bars, worst["revenue"], worst["avg_rating"], worst["return_pct"]):
    ax.text(r/1e6 + worst["revenue"].max()/1e6*0.02, b.get_y()+b.get_height()/2,
            f"{money(r)}  ★{rt}  ↩{rp}%", va="center", fontsize=8.5, color=K["clay"])
ax.set_title("Bottom 10 Products — the Long Tail", pad=14)
ax.set_xlabel("Revenue (R millions)")
ax.set_xlim(0, worst["revenue"].max()/1e6 * 1.3)
ax.tick_params(labelsize=8.5)
savefig(fig, "worst10_products.png")

# ═══════════════════════════════════════════════════════════════
# 3. CATEGORY TREEMAP (proper squarified layout)
# ═══════════════════════════════════════════════════════════════
import squarify
csorted = cats.sort_values("revenue", ascending=False).reset_index(drop=True)
W, H = 100.0, 62.0
rects = squarify.normalize_sizes(csorted["revenue"].values, W, H)
rects = squarify.squarify(rects, 0, 0, W, H)
fig, ax = plt.subplots(figsize=(11, 6.8))
ax.axis("off")
for r, (_, row), col in zip(rects, csorted.iterrows(), CAT12):
    ax.add_patch(FancyBboxPatch((r["x"]+0.4, r["y"]+0.4), r["dx"]-0.8, r["dy"]-0.8,
                 boxstyle="round,pad=0,rounding_size=0.7", facecolor=col,
                 edgecolor="white", linewidth=2.5))
    big = r["dx"] > 14 and r["dy"] > 12
    ax.text(r["x"]+r["dx"]/2, r["y"]+r["dy"]/2 + (1.8 if big else 0), row["category"],
            ha="center", va="center", color="white",
            fontsize=min(13, max(7, r["dx"]/4.5)), fontweight="bold", wrap=True)
    if big:
        ax.text(r["x"]+r["dx"]/2, r["y"]+r["dy"]/2 - 3.2, money(row["revenue"]),
                ha="center", va="center", color="white", fontsize=9.5)
        ax.text(r["x"]+r["dx"]/2, r["y"]+r["dy"]/2 - 6, f"{row['products']} products · ★{row['avg_rating']:.1f}",
                ha="center", va="center", color="white", fontsize=7.5, alpha=0.9)
ax.set_xlim(0, W); ax.set_ylim(0, H)
ax.invert_yaxis()
ax.set_title("Revenue by Category — the Product Mix", pad=12)
savefig(fig, "category_treemap.png")

# ═══════════════════════════════════════════════════════════════
# 4. TOP BRANDS (lollipop, coloured by category)
# ═══════════════════════════════════════════════════════════════
tb = brands.head(12).iloc[::-1]
catcolor = {c: CAT12[i] for i, c in enumerate(cats["category"])}
fig, ax = plt.subplots(figsize=(9.5, 6))
for i, (_, r) in enumerate(tb.iterrows()):
    col = catcolor.get(r["category"], K["ochre"])
    ax.plot([0, r["revenue"]/1e6], [i, i], color=col, lw=2.5, zorder=1)
    ax.scatter(r["revenue"]/1e6, i, s=160, color=col, zorder=2, edgecolor="white", linewidth=1.5)
    ax.text(r["revenue"]/1e6 + 12, i, f"{money(r['revenue'])}  ★{r['avg_rating']:.1f}",
            va="center", fontsize=8.5, color=K["ink"])
ax.set_yticks(range(len(tb)))
ax.set_yticklabels(tb["brand"], fontsize=9)
ax.set_title("Top 12 Brands by Revenue", pad=14)
ax.set_xlabel("Revenue (R millions)")
ax.set_xlim(0, tb["revenue"].max()/1e6 * 1.25)
savefig(fig, "top_brands.png")

# ═══════════════════════════════════════════════════════════════
# 5. SCATTER — price vs rating, bubble = revenue, colour = category
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6.5))
for i, cat in enumerate(cats["category"]):
    sub = products[products["category"] == cat]
    ax.scatter(sub["unit_price"], sub["avg_rating"], s=sub["revenue"]/1e6*3 + 15,
               color=CAT12[i], alpha=0.72, edgecolor="white", linewidth=0.7, label=cat)
ax.set_xscale("log")
ax.set_title("Price vs Customer Rating  (bubble = revenue)", pad=14)
ax.set_xlabel("Unit price (R, log scale)"); ax.set_ylabel("Average rating (★)")
ax.legend(fontsize=7.5, ncol=2, loc="lower right", framealpha=0.9)
ax.grid(True, alpha=0.2)
savefig(fig, "price_vs_rating.png")

# ═══════════════════════════════════════════════════════════════
# 6. RETURN RATE vs REVENUE (the margin-risk quadrant)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 6))
for i, cat in enumerate(cats["category"]):
    sub = products[products["category"] == cat]
    ax.scatter(sub["return_pct"], sub["revenue"]/1e6, s=70, color=CAT12[i],
               alpha=0.75, edgecolor="white", linewidth=0.7, label=cat)
med_ret = products["return_pct"].median()
ax.axvline(med_ret, ls="--", color=K["clay"], alpha=0.6)
ax.text(med_ret+0.2, ax.get_ylim()[1]*0.9, "median return rate", fontsize=8, color=K["clay"])
ax.set_title("Return Rate vs Revenue — Margin Risk Map", pad=14)
ax.set_xlabel("Return rate (%)"); ax.set_ylabel("Revenue (R millions)")
ax.legend(fontsize=7.5, ncol=2, loc="upper right", framealpha=0.9)
savefig(fig, "return_vs_revenue.png")

# ═══════════════════════════════════════════════════════════════
# 7. MONTHLY REVENUE — stacked area by top categories
# ═══════════════════════════════════════════════════════════════
piv = monthly_cat.pivot_table(index="order_month", columns="category",
                              values="revenue", aggfunc="sum").fillna(0)
piv = piv[cats.sort_values("revenue", ascending=False)["category"].tolist()]
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.stackplot(range(len(piv)), *[piv[c].values/1e6 for c in piv.columns],
             labels=piv.columns, colors=CAT12, alpha=0.9)
step = max(1, len(piv)//9)
ax.set_xticks(range(0, len(piv), step))
ax.set_xticklabels(piv.index[::step], rotation=45, ha="right", fontsize=8)
ax.set_title("Monthly Revenue by Category  (18 months)", pad=14)
ax.set_ylabel("Revenue (R millions)")
ax.legend(fontsize=7, ncol=4, loc="upper left", framealpha=0.9)
ax.set_xlim(0, len(piv)-1)
savefig(fig, "monthly_stacked.png")

# ═══════════════════════════════════════════════════════════════
# 8. SOUTH AFRICA PROVINCE CHOROPLETH (districts -> provinces)
# ═══════════════════════════════════════════════════════════════
DISTRICT_TO_PROV = {
    "City of Johannesburg Metropolitan": "Gauteng", "City of Tshwane Metropolitan": "Gauteng",
    "Ekurhuleni Metropolitan": "Gauteng", "Sedibeng District": "Gauteng", "West Rand District": "Gauteng",
    "Cape Winelands District": "Western Cape", "City of Cape Town": "Western Cape",
    "Central Karoo District": "Western Cape", "Eden District": "Western Cape",
    "Overberg District": "Western Cape", "West Coast District": "Western Cape",
    "Amajuba District": "KwaZulu-Natal", "eThekwini Metropolitan": "KwaZulu-Natal",
    "iLembe District": "KwaZulu-Natal", "Sisonke District": "KwaZulu-Natal", "Ugu District": "KwaZulu-Natal",
    "uMgungundlovu District": "KwaZulu-Natal", "Umkhanyakude District": "KwaZulu-Natal",
    "Umzinyathi District": "KwaZulu-Natal", "Uthukela District": "KwaZulu-Natal",
    "uThungulu District": "KwaZulu-Natal", "Zululand District": "KwaZulu-Natal",
    "Alfred Nzo District": "Eastern Cape", "Amathole District": "Eastern Cape",
    "Buffalo City Metropolitan": "Eastern Cape", "Chris Hani District": "Eastern Cape",
    "Joe Gqabi District": "Eastern Cape", "Nelson Mandela Bay Metropolitan": "Eastern Cape",
    "O.R. Tambo District": "Eastern Cape", "Sarah Baartman District": "Eastern Cape",
    "Fezile Dabi District": "Free State", "Lejweleputswa District": "Free State",
    "Mangaung Metropolitan": "Free State", "Thabo Mofutsanyana District": "Free State",
    "Xhariep District": "Free State",
    "Ehlanzeni District": "Mpumalanga", "Gert Sibande District": "Mpumalanga",
    "Nkangala District": "Mpumalanga",
    "Capricorn District": "Limpopo", "Mopani District": "Limpopo", "Sekhukhune District": "Limpopo",
    "Vhembe District": "Limpopo", "Waterberg District": "Limpopo",
    "Bojanala Platinum District": "North West", "Dr Kenneth Kaunda District": "North West",
    "Dr Ruth Segomotsi Mompati District": "North West", "Ngaka Modiri Molema District": "North West",
    "Frances Baard District": "Northern Cape", "John Taolo Gaetsewe District": "Northern Cape",
    "Namakwa District": "Northern Cape", "Pixley ka Seme District": "Northern Cape",
    "ZF Mgcawu District": "Northern Cape",
}
prov_rev = prov_cat.groupby("province")["revenue"].sum()

geo = json.loads((OUT / "sa_provinces.geojson").read_text(encoding="utf-8"))
# collect polygons per province
prov_polys = {}
for feat in geo["features"]:
    prov = DISTRICT_TO_PROV.get(feat["properties"]["name"])
    if not prov:
        continue
    geom = feat["geometry"]
    polys = geom["coordinates"] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
    rings = [geom["coordinates"][0]] if geom["type"] == "Polygon" else [poly[0] for poly in geom["coordinates"]]
    prov_polys.setdefault(prov, []).extend(rings)

fig, ax = plt.subplots(figsize=(11, 9))
ax.set_facecolor("#EAF2F5")  # subtle map-water backdrop
rev_vals = prov_rev.reindex(prov_polys.keys()).fillna(0)
norm = Normalize(rev_vals.min(), rev_vals.max())
CITY = {
    "Johannesburg": (28.05, -26.20), "Cape Town": (18.42, -33.92), "Durban": (31.02, -29.86),
    "Pretoria": (28.23, -25.75), "Gqeberha": (25.60, -33.96), "Bloemfontein": (26.16, -29.09),
    "Polokwane": (29.47, -23.90), "Mbombela": (30.99, -25.47), "Kimberley": (24.75, -28.73),
}
prov_centroids = {}
for prov, rings in prov_polys.items():
    verts = [np.array(r) for r in rings]
    pc = PolyCollection(verts, facecolor=KAROO_SEQ(norm(prov_rev.get(prov, 0))),
                        edgecolor="white", linewidth=1.4, alpha=0.95)
    ax.add_collection(pc)
    allpts = np.vstack(verts)
    prov_centroids[prov] = allpts.mean(axis=0)
# province labels + revenue
for prov, c in prov_centroids.items():
    r = prov_rev.get(prov, 0)
    ax.text(c[0], c[1], f"{prov}\n{money(r)}", ha="center", va="center", fontsize=7.5,
            fontweight="bold", color="white" if norm(r) > 0.5 else K["ink"],
            path_effects=None)
# city dots
for city, (lon, lat) in CITY.items():
    ax.plot(lon, lat, "o", ms=6, color=K["ink"], zorder=5)
    ax.plot(lon, lat, "o", ms=3, color="white", zorder=6)
ax.set_xlim(15.5, 33.5); ax.set_ylim(-35.5, -21.8)
ax.set_aspect(1.15)
ax.axis("off")
ax.set_title("Karoo Revenue by Province — where South Africa shops", fontsize=16, pad=10, color=K["ink"])
# colourbar
sm = plt.cm.ScalarMappable(cmap=KAROO_SEQ, norm=norm); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.01)
cb.set_label("Revenue (R)", color=K["clay"])
cb.ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: money(v)))
savefig(fig, "sa_choropleth.png")

print("All charts rendered to", CHARTS)
for f in sorted(CHARTS.glob("*.png")):
    print(" ", f.name)

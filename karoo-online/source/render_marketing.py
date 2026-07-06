"""Marketing + data-provenance charts for Karoo Online."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).parent
OUT = HERE / "out"
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


paid = pd.read_csv(OUT / "mkt_paid_by_channel.csv")
paid_m = pd.read_csv(OUT / "mkt_paid_campaigns.csv")
rm = pd.read_csv(OUT / "mkt_remarketing.csv")
seo = pd.read_csv(OUT / "mkt_seo_monthly.csv")
kw = pd.read_csv(OUT / "mkt_seo_keywords.csv")
ai_comp = pd.read_csv(OUT / "mkt_ai_competitors.csv")
ai_vis = pd.read_csv(OUT / "mkt_ai_visibility.csv")

# 1. Paid: spend vs revenue + ROAS
p = paid.sort_values("revenue")
fig, ax = plt.subplots(figsize=(10, 5))
y = np.arange(len(p))
ax.barh(y+0.2, p["spend"]/1e6, height=0.4, color=K["sand"], label="Spend", edgecolor=K["clay"])
ax.barh(y-0.2, p["revenue"]/1e6, height=0.4, color=K["ochre"], label="Revenue")
for i, (_, r) in enumerate(p.iterrows()):
    ax.text(r["revenue"]/1e6+0.1, i-0.2, f"ROAS {r['roas']:.1f}×", va="center", fontsize=9, fontweight="bold", color=K["teal"])
ax.set_yticks(y); ax.set_yticklabels(p["channel"]); ax.set_xlabel("R millions")
ax.set_title("Paid Campaigns — Spend vs Revenue by Channel"); ax.legend(loc="lower right")
save(fig, "mkt_paid.png")

# 2. Remarketing ROAS
r = rm.sort_values("roas")
fig, ax = plt.subplots(figsize=(9.5, 4.8))
colors = [K["green"] if v >= 10 else K["teal"] if v >= 6 else K["gold"] for v in r["roas"]]
bars = ax.barh(r["audience"], r["roas"], color=colors, edgecolor="white")
for b, v in zip(bars, r["roas"]):
    ax.text(v+0.2, b.get_y()+b.get_height()/2, f"{v:.1f}×", va="center", fontweight="bold", fontsize=10)
ax.set_title("Remarketing — Return on Ad Spend by Audience"); ax.set_xlabel("ROAS")
ax.set_xlim(0, r["roas"].max()*1.15)
save(fig, "mkt_remarketing.png")

# 3. SEO growth (organic sessions brand vs non-brand)
fig, ax = plt.subplots(figsize=(11, 5))
x = range(len(seo))
ax.stackplot(x, seo["nonbrand_sessions"]/1000, seo["brand_sessions"]/1000,
             labels=["Non-brand (discovery)", "Brand (loyalty)"], colors=[K["teal"], K["gold"]], alpha=0.9)
ax.set_xticks(list(x)[::2]); ax.set_xticklabels(seo["month"][::2], rotation=45, ha="right", fontsize=8)
ax.set_title("SEO — Organic Sessions Growth (thousands/month)"); ax.set_ylabel("Sessions (000s)")
ax.legend(loc="upper left"); ax.set_xlim(0, len(seo)-1)
save(fig, "mkt_seo.png")

# 4. Keyword ranking distribution — clearer: where we rank on Google + traffic each band drives
fig, ax = plt.subplots(figsize=(10, 5))
# colour by "goodness" of the position (top = green, page 2+ = muted)
kcolors = [K["green"], K["sage"], K["gold"], K["coral"], K["sand"]]
bars = ax.bar(kw["position"], kw["keywords"], color=kcolors, edgecolor="white", width=0.72)
for b, n, t in zip(bars, kw["keywords"], kw["traffic_share_pct"]):
    ax.text(b.get_x()+b.get_width()/2, n+50, f"{n:,} keywords", ha="center", fontsize=9, fontweight="bold")
    # traffic-share pill inside/above bar
    ax.text(b.get_x()+b.get_width()/2, n*0.5 if n > 500 else n+220,
            f"{t}%\nof traffic", ha="center", va="center", fontsize=8.5,
            color="white" if n > 500 else K["ink"],
            bbox=dict(boxstyle="round,pad=0.3", fc=K["ink"] if n > 500 else "none",
                      ec="none", alpha=0.75 if n > 500 else 0))
ax.set_title("Where Karoo Online Ranks on Google — and what each rank is worth", pad=22)
ax.text(0.5, 1.045, "Bars = how many of our keywords sit in each Google position band  ·  "
        "pill = share of organic traffic that band delivers",
        transform=ax.transAxes, ha="center", fontsize=9, color=K["clay"], style="italic")
ax.set_ylabel("Number of ranking keywords"); ax.set_xlabel("Google search position")
ax.set_ylim(0, kw["keywords"].max()*1.28)
# highlight the insight: page-1 (pos 1-10) drives most traffic despite few keywords
page1_traffic = kw.iloc[0]["traffic_share_pct"] + kw.iloc[1]["traffic_share_pct"]
ax.annotate(f"Positions 1–10 = only {kw.iloc[0]['keywords']+kw.iloc[1]['keywords']:,} keywords\n"
            f"but {page1_traffic}% of all organic traffic",
            xy=(0.5, kw.iloc[0]["keywords"]), xytext=(1.4, kw["keywords"].max()*1.0),
            fontsize=8.5, color=K["green"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=K["green"]))
save(fig, "mkt_keywords.png")

# 5. AI share of voice vs competitors
c = ai_comp.sort_values("ai_share_of_voice_pct")
fig, ax = plt.subplots(figsize=(9, 4.5))
colors = [K["ochre"] if n == "Karoo Online" else K["sand"] for n in c["retailer"]]
bars = ax.barh(c["retailer"], c["ai_share_of_voice_pct"], color=colors, edgecolor=K["clay"])
for b, v in zip(bars, c["ai_share_of_voice_pct"]):
    ax.text(v+0.5, b.get_y()+b.get_height()/2, f"{v}%", va="center", fontweight="bold")
ax.set_title("AI Visibility — Share of Voice in AI Answers vs Competitors")
ax.set_xlabel("Share of voice (%)"); ax.set_xlim(0, c["ai_share_of_voice_pct"].max()*1.2)
save(fig, "mkt_ai_sov.png")

# 6. AI visibility by platform
fig, ax = plt.subplots(figsize=(9.5, 4.5))
v = ai_vis.sort_values("share_of_voice_pct")
bars = ax.barh(v["platform"], v["share_of_voice_pct"], color=K["plum"], edgecolor="white")
for b, sov, pos in zip(bars, v["share_of_voice_pct"], v["avg_position"]):
    ax.text(sov+0.4, b.get_y()+b.get_height()/2, f"{sov}%  ·  avg pos {pos}", va="center", fontsize=8.5)
ax.set_title("AI Visibility — Presence Across AI Platforms")
ax.set_xlabel("Share of voice (%)"); ax.set_xlim(0, v["share_of_voice_pct"].max()*1.35)
save(fig, "mkt_ai_platforms.png")

# ══ 7. DATA PROVENANCE / LINEAGE DIAGRAM ══
fig, ax = plt.subplots(figsize=(13, 8))
ax.set_xlim(0, 13); ax.set_ylim(0, 8); ax.axis("off")


def box(x, y, w, h, title, sub, fc, tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12",
                 fc=fc, ec="white", lw=2))
    ax.text(x+w/2, y+h*0.62, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color=tc)
    ax.text(x+w/2, y+h*0.28, sub, ha="center", va="center", fontsize=7, color=tc)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                 lw=1.6, color=K["clay"], shrinkA=3, shrinkB=3))


ax.text(6.5, 7.6, "Where the Data Comes From — One Central Store, One Source of Truth",
        ha="center", fontsize=15, fontweight="bold", color=K["ink"])

# Sources (left)
sources = [("Catalogue Extract", "1,000 real products", K["ochre"], 6.3),
           ("GA4 Web", "sessions · funnel", K["teal"], 4.9),
           ("AppsFlyer", "installs · ad spend", K["sky"], 3.5),
           ("Orders", "1M transactions", K["sage"], 2.1),
           ("Marketing", "campaigns · SEO · AI", K["plum"], 0.7)]
ax.text(1.65, 7.35, "DATA SOURCES", ha="center", fontsize=9, fontweight="bold", color=K["clay"])
for t, s, c, y in sources:
    box(0.3, y, 2.7, 1.05, t, s, c)
    arrow(3.0, y+0.5, 4.2, 4.0)

# Central store (middle)
ax.add_patch(FancyBboxPatch((4.3, 2.2), 3.6, 3.6, boxstyle="round,pad=0.05,rounding_size=0.2",
             fc=K["ink"], ec=K["gold"], lw=3))
ax.text(6.1, 5.35, "CENTRAL LAKEHOUSE", ha="center", fontsize=11, fontweight="bold", color=K["gold"])
ax.text(6.1, 4.8, "Amazon S3  ·  AWS Glue Catalog", ha="center", fontsize=8.5, color="white")
ax.text(6.1, 4.35, "database: karoo_db", ha="center", fontsize=8, color="#cbb8a0", style="italic")
for i, tb in enumerate(["orders_curated (Parquet)", "ga4_events", "appsflyer_events", "products"]):
    ax.text(6.1, 3.9-i*0.42, f"|  {tb}", ha="center", fontsize=7.5, color="#e8d5c0")

# Analytics (right)
outs = [("KPIs & BI", K["ochre"], 6.0), ("Recommendations", K["teal"], 4.75),
        ("Fraud Detection", K["rust"], 3.5), ("Marketing ROAS", K["plum"], 2.25)]
ax.text(11.0, 7.35, "ANALYTICS", ha="center", fontsize=9, fontweight="bold", color=K["clay"])
for t, c, y in outs:
    box(9.4, y, 3.2, 1.0, t, "", c)
    arrow(7.9, 4.0, 9.4, y+0.5)

# decision arrow
ax.add_patch(FancyBboxPatch((9.4, 0.5), 3.2, 1.2, boxstyle="round,pad=0.03,rounding_size=0.12",
             fc=K["gold"], ec="white", lw=2))
ax.text(11.0, 1.35, "DECISIONS", ha="center", fontsize=11, fontweight="bold", color=K["ink"])
ax.text(11.0, 0.95, "act on the insight", ha="center", fontsize=7.5, color=K["ink"])
for _, _, y in outs:
    arrow(11.0, y, 11.0, 1.75)

save(fig, "data_provenance.png")
print("Marketing + provenance charts rendered.")

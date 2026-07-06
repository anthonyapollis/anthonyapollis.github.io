"""Full-spectrum marketing analytics for Karoo Online: paid campaigns
(cost/revenue/ROAS), remarketing, SEO, and AI-SEO / AI-visibility.
Realistic SA e-commerce benchmarks; outputs CSVs + a summary JSON."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2026)

MONTHS = pd.date_range("2025-01", "2026-06", freq="MS").strftime("%Y-%m").tolist()

# ── 1. PAID CAMPAIGNS (channel × month) ──
# (channel, avg_cpc, ctr, cvr, aov, monthly_spend_base) — cvr tuned so
# ROAS (= cvr*aov/cpc) lands in realistic 1.4-4.6 ranges per channel.
CHANNELS = [
    ("Google Search",   4.20, 0.045, 0.0222, 720, 42000),
    ("Google Shopping", 3.10, 0.012, 0.0207, 690, 55000),
    ("Facebook Ads",    2.30, 0.009, 0.0102, 540, 38000),
    ("Instagram Ads",   2.80, 0.011, 0.0140, 520, 26000),
    ("TikTok Ads",      1.60, 0.014, 0.0073, 460, 22000),
    ("Apple Search Ads",5.40, 0.030, 0.0093, 810, 12000),
]
paid = []
for i, m in enumerate(MONTHS):
    season = 1.0 + 0.35 * np.exp(-((i - 15) ** 2) / 8)  # festive ramp toward Nov/Dec
    for ch, cpc, ctr, cvr, aov, base in CHANNELS:
        spend = base * season * rng.uniform(0.9, 1.1)
        clicks = spend / cpc
        impressions = clicks / ctr
        conversions = clicks * cvr * rng.uniform(0.9, 1.1)
        revenue = conversions * aov * rng.uniform(0.95, 1.08)
        paid.append({
            "month": m, "channel": ch, "impressions": int(impressions), "clicks": int(clicks),
            "spend": round(spend, 0), "conversions": int(conversions), "revenue": round(revenue, 0),
            "ctr_pct": round(ctr * 100, 2), "cvr_pct": round(cvr * 100, 2),
            "cpc": round(cpc, 2), "roas": round(revenue / spend, 2),
            "cpa": round(spend / max(conversions, 1), 0),
        })
paid_df = pd.DataFrame(paid)
paid_df.to_csv(OUT / "mkt_paid_campaigns.csv", index=False)
paid_channel = paid_df.groupby("channel").agg(
    spend=("spend", "sum"), revenue=("revenue", "sum"), conversions=("conversions", "sum"),
    impressions=("impressions", "sum"), clicks=("clicks", "sum")).reset_index()
paid_channel["roas"] = (paid_channel["revenue"] / paid_channel["spend"]).round(2)
paid_channel["cpa"] = (paid_channel["spend"] / paid_channel["conversions"]).round(0)
paid_channel["ctr_pct"] = (100 * paid_channel["clicks"] / paid_channel["impressions"]).round(2)
paid_channel = paid_channel.sort_values("revenue", ascending=False)
paid_channel.to_csv(OUT / "mkt_paid_by_channel.csv", index=False)

# ── 2. REMARKETING ──
REMARKET = [
    ("Cart Abandoners", 18000, 11.5, "Recover started-but-unfinished checkouts"),
    ("Product Viewers", 24000, 5.8, "Re-engage browsers who viewed but didn't add"),
    ("Past Purchasers (Winback)", 15000, 7.2, "Bring back lapsed customers"),
    ("Email Flows (automated)", 4000, 19.5, "Abandoned-cart & post-purchase email"),
    ("Push / App Re-engagement", 6000, 6.4, "Notify app users of price drops & restocks"),
]
rm = []
for name, spend, roas, desc in REMARKET:
    rev = spend * roas * rng.uniform(0.95, 1.05)
    rm.append({"audience": name, "spend": spend, "revenue": round(rev, 0),
               "roas": round(rev / spend, 1), "description": desc})
rm_df = pd.DataFrame(rm).sort_values("roas", ascending=False)
rm_df.to_csv(OUT / "mkt_remarketing.csv", index=False)

# ── 3. SEO ──
seo_monthly = []
for i, m in enumerate(MONTHS):
    growth = 1.0 + i * 0.035  # steady organic growth
    season = 1.0 + 0.30 * np.exp(-((i - 15) ** 2) / 8)
    organic = int(48000 * growth * season * rng.uniform(0.96, 1.04))
    brand = int(organic * rng.uniform(0.28, 0.34))
    seo_monthly.append({"month": m, "organic_sessions": organic, "brand_sessions": brand,
                        "nonbrand_sessions": organic - brand,
                        "organic_revenue": round(organic * 0.028 * 560, 0)})
seo_df = pd.DataFrame(seo_monthly)
seo_df.to_csv(OUT / "mkt_seo_monthly.csv", index=False)

# keyword ranking distribution
kw_buckets = pd.DataFrame({
    "position": ["1-3 (top)", "4-10 (page 1)", "11-20 (page 2)", "21-50", "51-100"],
    "keywords": [412, 1180, 1640, 3210, 2050],
    "traffic_share_pct": [46, 31, 12, 8, 3],
})
kw_buckets.to_csv(OUT / "mkt_seo_keywords.csv", index=False)

top_pages = pd.DataFrame({
    "landing_page": ["/electronics/laptops", "/home-kitchen/air-fryers", "/deals/black-friday",
                     "/baby/strollers", "/sport/home-gym", "/beauty/skincare", "/", "/automotive/car-care"],
    "organic_sessions": [8200, 6900, 12400, 4100, 3800, 3500, 15600, 2900],
    "conversion_pct": [3.8, 5.2, 6.1, 4.4, 3.1, 4.8, 2.2, 3.6],
})
top_pages["revenue"] = (top_pages["organic_sessions"] * top_pages["conversion_pct"] / 100 * 610).round(0)
top_pages = top_pages.sort_values("revenue", ascending=False)
top_pages.to_csv(OUT / "mkt_seo_pages.csv", index=False)

# ── 4. AI-SEO / AI VISIBILITY ──
# How often Karoo Online is surfaced/cited in AI assistant answers vs competitors
ai_visibility = pd.DataFrame({
    "platform": ["Google AI Overviews", "ChatGPT", "Perplexity", "Gemini", "Bing Copilot"],
    "karoo_citations": [340, 210, 185, 160, 95],
    "share_of_voice_pct": [22, 18, 26, 15, 12],
    "avg_position": [2.3, 2.8, 1.9, 3.1, 3.4],
    "sentiment": ["Positive", "Positive", "Positive", "Neutral", "Neutral"],
})
ai_visibility.to_csv(OUT / "mkt_ai_visibility.csv", index=False)

ai_competitors = pd.DataFrame({
    "retailer": ["Takealot", "Amazon.co.za", "Karoo Online", "Makro", "Loot"],
    "ai_share_of_voice_pct": [41, 23, 19, 11, 6],
})
ai_competitors.to_csv(OUT / "mkt_ai_competitors.csv", index=False)

# AI-cited query themes (where the brand shows up in AI answers)
ai_queries = pd.DataFrame({
    "query_theme": ["best online store South Africa", "cheapest laptop deals SA",
                    "where to buy air fryer", "black friday deals SA", "baby products online SA"],
    "karoo_cited_pct": [24, 31, 38, 45, 28],
})
ai_queries.to_csv(OUT / "mkt_ai_queries.csv", index=False)

# ── Summary ──
total_paid_spend = paid_df["spend"].sum()
total_paid_rev = paid_df["revenue"].sum()
total_rm_spend = rm_df["spend"].sum()
total_rm_rev = rm_df["revenue"].sum()
total_seo_rev = seo_df["organic_revenue"].sum()
blended_roas = (total_paid_rev + total_rm_rev) / (total_paid_spend + total_rm_spend)
summary = {
    "paid_spend": round(total_paid_spend), "paid_revenue": round(total_paid_rev),
    "paid_roas": round(total_paid_rev / total_paid_spend, 2),
    "best_paid_channel": paid_channel.iloc[0]["channel"],
    "best_paid_roas": float(paid_channel["roas"].max()),
    "best_paid_channel_by_roas": paid_channel.sort_values("roas", ascending=False).iloc[0]["channel"],
    "remarketing_spend": round(total_rm_spend), "remarketing_revenue": round(total_rm_rev),
    "remarketing_roas": round(total_rm_rev / total_rm_spend, 1),
    "best_remarketing": rm_df.iloc[0]["audience"], "best_remarketing_roas": float(rm_df["roas"].max()),
    "seo_revenue": round(total_seo_rev),
    "seo_sessions_latest": int(seo_df.iloc[-1]["organic_sessions"]),
    "seo_page1_keywords": int(kw_buckets.iloc[0]["keywords"] + kw_buckets.iloc[1]["keywords"]),
    "blended_roas": round(blended_roas, 2),
    "ai_share_of_voice": int(ai_competitors[ai_competitors.retailer == "Karoo Online"]["ai_share_of_voice_pct"].iloc[0]),
    "total_marketing_revenue": round(total_paid_rev + total_rm_rev + total_seo_rev),
    "total_marketing_spend": round(total_paid_spend + total_rm_spend),
}
json.dump(summary, open(OUT / "mkt_summary.json", "w"), indent=2)
print("Marketing analytics complete.")
for k, v in summary.items():
    print(f"  {k}: {v}")

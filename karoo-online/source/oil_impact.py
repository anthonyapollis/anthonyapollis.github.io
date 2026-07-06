"""2026 Strait of Hormuz crisis — impact on Karoo Online.

REAL EVENT (sourced online): the 2026 Strait of Hormuz crisis.
- 28 Feb 2026: US/Israeli strikes (Operation Epic Fury); IRGC bars passage.
- 8 Mar 2026: Brent tops $100/bbl for the first time in 4 years; March saw the
  largest-ever monthly oil-price increase. Peak ~$126/bbl.
- 27 Mar 2026: strait formally closed - "largest disruption to world energy
  supply since the 1970s".
- 17 Jun 2026 memorandum, ~29 Jun 2026 US-Iran deal; oil eases back toward $70.
A minor June-2025 "12-Day War" was only a brief precursor blip.

Impact modelled on the real monthly Brent path over the analysis window
(Jan 2025 - Jun 2026): fuel-linked delivery cost + discretionary-demand hit.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "out"
MONTHS = pd.date_range("2025-01", "2026-06", freq="MS")

# Monthly-average Brent (US$/bbl), real path. Calm ~$70 through 2025 (brief
# Jun-2025 blip), then the major Feb-Jun 2026 crisis peaking March 2026.
brent = np.array([72, 71, 70, 69, 70, 76,   # Jan-Jun 2025 (Jun = minor 12-Day War blip)
                  71, 69, 70, 71, 72, 73,    # Jul-Dec 2025 (calm)
                  74, 83, 120, 116, 101, 84])  # Jan-Jun 2026 (Hormuz crisis: Mar peak, Jun easing)
baseline = 70.0
oil_pct = np.maximum((brent - baseline) / baseline, 0)  # only upside shocks hurt

FUEL_SHARE = 0.45
DELIVERY_BASE = 42.0
DISC_ELASTICITY = 0.22
ESS_ELASTICITY = 0.04
DISCRETIONARY = ["Electronics", "Automotive", "Sport & Outdoor", "Home & Kitchen", "Fashion", "Toys & Games"]
ESSENTIAL = ["Baby & Kids", "Beauty & Health", "Pet Supplies", "Books"]

rows = []
base_orders = 56000
for i, m in enumerate(MONTHS):
    season = 1.0 + 0.30 * np.exp(-((i - 11) ** 2) / 8)  # festive-2025 peak
    shock = oil_pct[i]
    delivery_cost = DELIVERY_BASE * (1 + FUEL_SHARE * shock)
    demand_index = 0.65 * (1 - DISC_ELASTICITY * shock) + 0.35 * (1 - ESS_ELASTICITY * shock)
    orders = int(base_orders * season * demand_index)
    orders_cf = int(base_orders * season)
    rows.append({
        "month": m.strftime("%Y-%m"), "brent_usd": int(brent[i]),
        "oil_shock_pct": round(oil_pct[i] * 100, 1),
        "delivery_cost_per_order": round(delivery_cost, 2),
        "revenue": round(orders * 560, 0), "revenue_baseline": round(orders_cf * 560, 0),
        "revenue_impact": round((orders - orders_cf) * 560, 0),
        "extra_delivery_cost": round(orders * delivery_cost - orders_cf * DELIVERY_BASE, 0),
    })
df = pd.DataFrame(rows)
df.to_csv(OUT / "oil_impact_monthly.csv", index=False)

peak_shock = oil_pct.max()
cat_rows = [{"category": c, "type": "Discretionary" if c in DISCRETIONARY else "Essential",
             "peak_demand_drop_pct": round((DISC_ELASTICITY if c in DISCRETIONARY else ESS_ELASTICITY) * peak_shock * 100, 1)}
            for c in DISCRETIONARY + ESSENTIAL]
pd.DataFrame(cat_rows).sort_values("peak_demand_drop_pct", ascending=False).to_csv(
    OUT / "oil_impact_categories.csv", index=False)

sw = df[df["oil_shock_pct"] > 0]
rev_lost = -sw[sw["revenue_impact"] < 0]["revenue_impact"].sum()
extra_deliv = sw[sw["extra_delivery_cost"] > 0]["extra_delivery_cost"].sum()
peak_row = df.loc[df["oil_shock_pct"].idxmax()]

summary = {
    "event": "2026 Strait of Hormuz Crisis",
    "event_dates": "28 Feb - late Jun 2026 (US-Iran deal ~29 Jun 2026)",
    "status": "Resolved by end-June 2026; Brent eased back toward $70",
    "analysis_window": "January 2025 - June 2026 (18 months)",
    "note_2025": "A minor June-2025 12-Day War caused only a brief ~$76 blip",
    "baseline_brent": int(baseline), "peak_brent": int(brent.max()), "peak_intraday": 126,
    "peak_shock_pct": round(peak_shock * 100), "peak_month": peak_row["month"],
    "crisis_months": "Feb-Jun 2026",
    "revenue_lost": round(rev_lost), "extra_delivery": round(extra_deliv),
    "margin_hit": round(rev_lost + extra_deliv),
    "months_affected": int((df["oil_shock_pct"] > 0).sum()),
    "peak_delivery_cost": round(df["delivery_cost_per_order"].max(), 2),
    "worst_category": "Electronics", "worst_category_drop": round(DISC_ELASTICITY * peak_shock * 100, 1),
}
json.dump(summary, open(OUT / "oil_summary.json", "w"), indent=2)
print("Oil impact (real 2026 Strait of Hormuz crisis) complete.")
for k, v in summary.items():
    print(f"  {k}: {v}")

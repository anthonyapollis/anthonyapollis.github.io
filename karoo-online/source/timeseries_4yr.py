"""Unified 4-year monthly time-series for Karoo Online (Jul 2022 - Jun 2026,
48 months). One coherent dataset feeding every time-based chart, so the
reporting is in unison. Includes growth, yearly festive seasonality, the
COVID-recovery era, and the 2026 Strait of Hormuz oil crisis."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "out"
rng = np.random.default_rng(2022)
MONTHS = pd.date_range("2022-07", "2026-06", freq="MS")

# Real Brent monthly-avg path (US$/bbl) across the 4 years, ending in the
# 2026 Strait of Hormuz crisis (peak ~$120 Mar 2026).
brent = np.array([
    105, 95, 90, 93, 91, 81,            # H2 2022 (post-Ukraine highs easing)
    83, 83, 79, 85, 76, 75,             # H1 2023
    80, 86, 89, 91, 83, 78,             # H2 2023
    82, 83, 85, 88, 82, 82,             # H1 2024
    80, 79, 74, 76, 74, 73,             # H2 2024
    72, 71, 70, 69, 70, 76,             # H1 2025 (Jun = minor 12-Day War blip)
    71, 69, 70, 71, 72, 73,             # H2 2025
    74, 83, 120, 116, 101, 84,          # H1 2026 (Hormuz crisis, Mar peak)
])
baseline_oil = 75.0

rows = []
base_rev = 22.0  # R millions/month at series start
for i, m in enumerate(MONTHS):
    t = i / 12.0
    growth = (1.20) ** t          # ~20%/yr compound growth
    festive = 1.0 + 0.28 * np.exp(-((m.month - 11.5) ** 2) / 3.0)  # Nov/Dec peak each year
    oil_shock = max((brent[i] - baseline_oil) / baseline_oil, 0)
    demand_drag = 1 - 0.18 * oil_shock  # discretionary demand softens when oil spikes
    revenue = base_rev * growth * festive * demand_drag * rng.uniform(0.97, 1.03)
    orders = revenue * 1e6 / 560
    # channels
    paid_spend = revenue * 0.085 * rng.uniform(0.95, 1.05)
    paid_rev = paid_spend * (3.3 + 0.3 * np.sin(t))   # ROAS ~3.3
    seo_sessions = 42000 * growth * festive * rng.uniform(0.96, 1.04)
    remarketing_rev = revenue * 0.045
    rows.append({
        "month": m.strftime("%Y-%m"), "year": m.year,
        "revenue_m": round(revenue, 2), "orders": int(orders),
        "brent_usd": int(brent[i]), "oil_shock_pct": round(oil_shock * 100, 1),
        "paid_spend_m": round(paid_spend, 2), "paid_revenue_m": round(paid_rev, 2),
        "seo_sessions": int(seo_sessions), "remarketing_revenue_m": round(remarketing_rev, 2),
        "aov": round(560 * rng.uniform(0.97, 1.03), 0),
    })

df = pd.DataFrame(rows)
df.to_csv(OUT / "timeseries_4yr.csv", index=False)

summary = {
    "start": MONTHS[0].strftime("%b %Y"), "end": MONTHS[-1].strftime("%b %Y"),
    "months": len(df), "years": 4,
    "total_revenue_bn": round(df["revenue_m"].sum() / 1000, 2),
    "cagr_pct": round(((df[df.year == 2025]["revenue_m"].sum() /
                        df[df.year == 2023]["revenue_m"].sum()) ** (1/2) - 1) * 100),
    "latest_month_rev_m": round(df.iloc[-1]["revenue_m"], 1),
    "peak_month": df.loc[df["revenue_m"].idxmax(), "month"],
}
json.dump(summary, open(OUT / "timeseries_summary.json", "w"), indent=2)
print("4-year time-series built.")
for k, v in summary.items():
    print(f"  {k}: {v}")

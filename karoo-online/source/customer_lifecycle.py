"""Customer lifetime cycle, churn and CLV for Karoo Online.
Generates a temporally-realistic customer base (signup dates, order history
over 18 months) and derives lifecycle stages, churn, CLV and cohort retention."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "out"
rng = np.random.default_rng(21)

N = 80_000
ASOF = pd.Timestamp("2026-06-30")
START = pd.Timestamp("2025-01-01")

# each customer: signup date, base order frequency, avg order value, loyalty
signup = START + pd.to_timedelta(rng.integers(0, 540, N), unit="D")
freq = rng.gamma(2.2, 1.3, N)                 # orders per month propensity
aov = np.round(rng.lognormal(6.1, 0.55, N), 2)  # ~R450 median
loyalty = rng.beta(2, 3, N)                    # 0-1 retention strength

rows = []
for i in range(N):
    months_active_possible = max(1, (ASOF - signup[i]).days / 30.4)
    # customers churn probabilistically over time (survival)
    churn_hazard = 0.06 * (1 - loyalty[i])     # monthly churn chance
    n_months = 0
    orders = 0
    for m in range(int(months_active_possible)):
        if rng.random() < churn_hazard and m > 0:
            break
        n_months = m + 1
        orders += rng.poisson(freq[i] * (0.6 + loyalty[i]))
    orders = max(1, orders)
    last_order_offset = rng.integers(0, max(1, int((ASOF - signup[i]).days * (n_months / months_active_possible))) + 1)
    last_order = signup[i] + pd.Timedelta(days=int((ASOF - signup[i]).days * (n_months / months_active_possible)))
    recency_days = (ASOF - last_order).days
    revenue = round(orders * aov[i] * rng.uniform(0.9, 1.1), 2)
    tenure_days = max(1, (last_order - signup[i]).days)
    rows.append({
        "customer_id": i, "signup": signup[i].strftime("%Y-%m"),
        "orders": orders, "revenue": revenue, "aov": round(revenue / orders, 2),
        "recency_days": int(recency_days), "tenure_days": tenure_days,
        "months_active": n_months, "loyalty": round(loyalty[i], 3),
    })

df = pd.DataFrame(rows)

# ── Lifecycle stage ──
def stage(r):
    if r["recency_days"] <= 30 and r["orders"] <= 2:
        return "New"
    if r["recency_days"] <= 60:
        return "Active"
    if r["recency_days"] <= 120:
        return "At Risk"
    if r["recency_days"] <= 240:
        return "Dormant"
    return "Churned"
df["lifecycle_stage"] = df.apply(stage, axis=1)
df["churned"] = (df["recency_days"] > 120).astype(int)

# ── CLV (predictive: monthly value × expected remaining lifetime) ──
df["monthly_value"] = df["revenue"] / (df["months_active"].clip(lower=1))
# expected lifetime from loyalty (1/hazard), capped
df["expected_lifetime_months"] = (1 / (0.06 * (1 - df["loyalty"]) + 0.01)).clip(upper=48)
df["clv"] = (df["monthly_value"] * df["expected_lifetime_months"]).round(2)

df.to_csv(OUT / "cust_lifecycle.csv", index=False)

# ── Aggregations ──
stage_order = ["New", "Active", "At Risk", "Dormant", "Churned"]
stage_sum = df.groupby("lifecycle_stage").agg(
    customers=("customer_id", "count"), revenue=("revenue", "sum"),
    avg_clv=("clv", "mean"), avg_orders=("orders", "mean")).reindex(stage_order).reset_index()
stage_sum.to_csv(OUT / "lifecycle_stages.csv", index=False)

# cohort retention: signup month × months-since, % still active
coh = []
for cohort, g in df.groupby("signup"):
    size = len(g)
    for m in range(0, 13):
        active = (g["months_active"] > m).sum()
        coh.append({"cohort": cohort, "month_offset": m, "retention_pct": round(100 * active / size, 1)})
cohort_df = pd.DataFrame(coh)
cohort_df.to_csv(OUT / "cohort_retention.csv", index=False)

# CLV distribution buckets
df["clv_band"] = pd.cut(df["clv"], [0, 1000, 3000, 6000, 12000, 1e9],
                        labels=["<R1k", "R1-3k", "R3-6k", "R6-12k", "R12k+"])
clv_band = df.groupby("clv_band", observed=True).agg(
    customers=("customer_id", "count"), total_clv=("clv", "sum")).reset_index()
clv_band.to_csv(OUT / "clv_bands.csv", index=False)

summary = {
    "customers": N,
    "churn_rate_pct": round(100 * df["churned"].mean(), 1),
    "avg_clv": round(df["clv"].mean()),
    "median_clv": round(df["clv"].median()),
    "total_clv_bn": round(df["clv"].sum() / 1e9, 2),
    "champions_clv": round(df.nlargest(int(N*0.1), "clv")["clv"].sum() / df["clv"].sum() * 100),
    "at_risk_customers": int((df["lifecycle_stage"] == "At Risk").sum()),
    "at_risk_revenue": round(df[df["lifecycle_stage"] == "At Risk"]["revenue"].sum() / 1e6),
    "avg_lifespan_months": round(df["months_active"].mean(), 1),
    "m1_retention": round(cohort_df[cohort_df.month_offset == 1]["retention_pct"].mean(), 0),
    "m6_retention": round(cohort_df[cohort_df.month_offset == 6]["retention_pct"].mean(), 0),
}
json.dump(summary, open(OUT / "lifecycle_summary.json", "w"), indent=2)
print("Customer lifecycle / churn / CLV complete.")
for k, v in summary.items():
    print(f"  {k}: {v}")
print("\nStages:")
print(stage_sum.to_string(index=False))

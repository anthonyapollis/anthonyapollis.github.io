"""Generate a behaviourally-realistic transaction dataset (home provinces,
category affinities, causal delivery/return links, injected fraud) and run
correlations, market-basket recommendations, and fraud detection on it.

This replaces the independent-random synthetic data for the behavioural
analyses, so lift, correlations and fraud signals are genuine and
interpretable. Product catalogue analysis uses the real catalogue data.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from itertools import combinations

OUT = Path(__file__).parent / "out"
rng = np.random.default_rng(7)

N_CUST = 80_000
CATEGORIES = ["Electronics", "Home & Kitchen", "Fashion", "Beauty & Health", "Toys & Games",
              "Sport & Outdoor", "Baby & Kids", "Automotive", "Pet Supplies", "Books"]
PROVINCES = ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State",
             "Mpumalanga", "Limpopo", "North West", "Northern Cape"]
PROV_W = [0.34, 0.22, 0.16, 0.07, 0.05, 0.05, 0.04, 0.04, 0.03]
COURIERS = ["CourierIT", "RAM", "DSV", "Fastway", "PargoPoint"]

# ── Real category affinities (which categories co-occur) ──
# Segments give customers a shopping "personality" -> real market-basket structure
SEGMENTS = {
    "Young Family":   ["Baby & Kids", "Toys & Games", "Home & Kitchen", "Fashion"],
    "Tech Enthusiast": ["Electronics", "Sport & Outdoor", "Automotive", "Books"],
    "Home Maker":     ["Home & Kitchen", "Beauty & Health", "Pet Supplies", "Fashion"],
    "Active Outdoors": ["Sport & Outdoor", "Automotive", "Electronics", "Pet Supplies"],
    "Value Shopper":  ["Books", "Beauty & Health", "Home & Kitchen", "Toys & Games"],
}
SEG_NAMES = list(SEGMENTS.keys())

# ── Build customers ──
seg = rng.choice(SEG_NAMES, N_CUST, p=[0.24, 0.20, 0.22, 0.18, 0.16])
home = rng.choice(PROVINCES, N_CUST, p=PROV_W)
is_fraud = rng.random(N_CUST) < 0.015  # 1.5% injected fraud

orders = []
for cid in range(N_CUST):
    fraud = is_fraud[cid]
    aff = SEGMENTS[seg[cid]]
    n_orders = rng.integers(6, 20) if not fraud else rng.integers(15, 40)  # fraud = high velocity
    home_prov = home[cid]
    for _ in range(n_orders):
        # 75% from affinity set (co-purchase structure), 25% random
        cat = rng.choice(aff) if rng.random() < 0.75 else rng.choice(CATEGORIES)
        # province: normally home; fraud ships all over
        prov = home_prov if (not fraud and rng.random() < 0.85) else rng.choice(PROVINCES)
        metro = prov in ("Gauteng", "Western Cape", "KwaZulu-Natal")
        courier = rng.choice(COURIERS)
        base_price = {"Electronics": 900, "Home & Kitchen": 500, "Fashion": 320, "Beauty & Health": 260,
                      "Toys & Games": 300, "Sport & Outdoor": 480, "Baby & Kids": 380, "Automotive": 560,
                      "Pet Supplies": 240, "Books": 180}[cat]
        price = round(rng.lognormal(0, 0.5) * base_price, 2)
        discount = rng.choice([0, 0, 5, 10, 15, 25], p=[0.4, 0.2, 0.15, 0.12, 0.08, 0.05])
        # discount drives qty (real elasticity)
        qty = 1 + rng.poisson(0.3 + discount * 0.04)
        promised = rng.choice([2, 3, 3, 4, 5])
        # delivery days ~ courier base + distance(non-metro penalty) + noise (causal)
        courier_base = {"CourierIT": 2.4, "RAM": 3.1, "DSV": 2.7, "Fastway": 3.6, "PargoPoint": 4.0}[courier]
        actual = max(1, round(rng.normal(courier_base + (0 if metro else 2.0), 1.0)))
        late = actual > promised
        # returns ~ late delivery + fashion + fraud (causal)
        p_return = 0.03 + (0.10 if late else 0) + (0.12 if cat == "Fashion" else 0) + (0.35 if fraud else 0)
        returned = int(rng.random() < min(p_return, 0.95))
        orders.append((cid, seg[cid], home_prov, prov, int(metro), cat, courier, price,
                       discount, qty, promised, actual, int(late), returned, int(fraud)))

df = pd.DataFrame(orders, columns=["customer_id", "segment", "home_province", "province", "is_metro",
                                   "category", "courier", "price", "discount_pct", "qty", "promised_days",
                                   "actual_days", "late", "returned", "is_fraud_true"])
df["net_revenue"] = (df["price"] * df["qty"] * (1 - df["discount_pct"] / 100)).round(2)
print(f"Generated {len(df):,} realistic orders, {N_CUST:,} customers")

# ══ 1. CORRELATIONS (now causal & interpretable) ══
corr = df[["price", "discount_pct", "qty", "promised_days", "actual_days", "late",
           "returned", "is_metro", "net_revenue"]].corr().round(3)
corr.to_csv(OUT / "rb_correlation_matrix.csv")
print("\nKey correlations:")
print(f"  discount -> qty:      {corr.loc['discount_pct','qty']:+.3f}  (promotions lift basket size)")
print(f"  late -> returned:     {corr.loc['late','returned']:+.3f}  (slow delivery drives returns)")
print(f"  is_metro -> actual:   {corr.loc['is_metro','actual_days']:+.3f}  (metros deliver faster)")

# ══ 2. MARKET BASKET (real lift now) ══
cust_cats = df.groupby("customer_id")["category"].apply(set)
n_cust = len(cust_cats)
cat_count = {c: 0 for c in CATEGORIES}
for s in cust_cats:
    for c in s:
        cat_count[c] += 1
pair_count = {}
for s in cust_cats:
    for a, b in combinations(sorted(s), 2):
        pair_count[(a, b)] = pair_count.get((a, b), 0) + 1
rules = []
for (a, b), pc in pair_count.items():
    lift = (pc * n_cust) / (cat_count[a] * cat_count[b])
    conf = pc / cat_count[a]
    rules.append({"antecedent": a, "consequent": b, "pair_customers": pc,
                  "confidence": round(conf, 3), "lift": round(lift, 3)})
rules_df = pd.DataFrame(rules).sort_values("lift", ascending=False)
rules_df.to_csv(OUT / "rb_recommendations.csv", index=False)
print(f"\nTop product recommendations (by lift):")
print(rules_df.head(6).to_string(index=False))

# ══ 3. FRAUD DETECTION (measurable precision/recall now) ══
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score

cust = df.groupby("customer_id").agg(
    orders=("category", "count"), total_spend=("net_revenue", "sum"),
    avg_order_value=("net_revenue", "mean"), return_rate=("returned", "mean"),
    n_provinces=("province", "nunique"), avg_discount=("discount_pct", "mean"),
    max_qty=("qty", "max"), is_fraud=("is_fraud_true", "max"),
).reset_index()

feats = ["orders", "total_spend", "avg_order_value", "return_rate", "n_provinces", "avg_discount", "max_qty"]
iso = IsolationForest(n_estimators=150, contamination=0.02, random_state=42, n_jobs=-1)
cust["iso_flag"] = (iso.fit_predict(cust[feats]) == -1).astype(int)
prec = precision_score(cust["is_fraud"], cust["iso_flag"])
rec = recall_score(cust["is_fraud"], cust["iso_flag"])

# interpretable rule flags
cust["flag_return_abuse"] = (cust["return_rate"] > 0.30).astype(int)
cust["flag_velocity"] = (cust["orders"] > cust["orders"].quantile(0.98)).astype(int)
cust["flag_multi_province"] = (cust["n_provinces"] >= 6).astype(int)
cust["risk_score"] = cust[["iso_flag", "flag_return_abuse", "flag_velocity", "flag_multi_province"]].sum(axis=1)
cust.to_csv(OUT / "rb_fraud_scored.csv", index=False)

fraud_summary = pd.DataFrame({
    "signal": ["ML anomaly (IsolationForest)", "Return abuse >30%", "High velocity (top 2%)",
               "Ships to 6+ provinces", "Review queue (2+ signals)"],
    "flagged": [cust["iso_flag"].sum(), cust["flag_return_abuse"].sum(), cust["flag_velocity"].sum(),
                cust["flag_multi_province"].sum(), (cust["risk_score"] >= 2).sum()],
})
fraud_summary["captures_real_fraud"] = [
    cust[cust[c] == 1]["is_fraud"].sum() for c in
    ["iso_flag", "flag_return_abuse", "flag_velocity", "flag_multi_province"]] + [
    cust[cust["risk_score"] >= 2]["is_fraud"].sum()]
fraud_summary.to_csv(OUT / "rb_fraud_summary.csv", index=False)

import json
json.dump({
    "n_orders": len(df), "n_customers": int(n_cust),
    "true_fraud": int(cust["is_fraud"].sum()), "fraud_pct": round(100*cust["is_fraud"].mean(), 2),
    "iso_precision": round(prec, 3), "iso_recall": round(rec, 3),
    "corr_discount_qty": float(corr.loc["discount_pct", "qty"]),
    "corr_late_return": float(corr.loc["late", "returned"]),
    "corr_metro_delivery": float(corr.loc["is_metro", "actual_days"]),
    "top_rule": f"{rules_df.iloc[0]['antecedent']} + {rules_df.iloc[0]['consequent']}",
    "top_lift": float(rules_df.iloc[0]["lift"]),
    "review_queue": int((cust["risk_score"] >= 2).sum()),
    "review_queue_fraud": int(cust[cust["risk_score"] >= 2]["is_fraud"].sum()),
}, open(OUT / "rb_summary.json", "w"), indent=2)

print(f"\nFraud: {cust['is_fraud'].sum()} true fraudsters ({100*cust['is_fraud'].mean():.1f}%)")
print(f"IsolationForest precision={prec:.2f}, recall={rec:.2f}")
print(fraud_summary.to_string(index=False))
print("\nSaved realistic behavioural analytics to", OUT)

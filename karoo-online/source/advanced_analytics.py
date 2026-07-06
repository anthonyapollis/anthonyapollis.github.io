"""Correlations, fraud detection, and recommendations — grounded in the
10M-row transactional lakehouse (Athena) + local ML."""
import io
import time
from pathlib import Path

import boto3
import numpy as np
import pandas as pd

REGION = "eu-north-1"
WORKGROUP = "karoo-wg"
ATHENA_BUCKET = "karoo-athena-results-a7227216"
RAW_BUCKET = "karoo-raw-a7227216"
OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

athena = boto3.client("athena", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def run(sql, label):
    qid = athena.start_query_execution(QueryString=sql, WorkGroup=WORKGROUP,
                                       QueryExecutionContext={"Database": "karoo_db"})["QueryExecutionId"]
    while True:
        info = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        st = info["Status"]["State"]
        if st in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    print(f"[{label}] {st} ({info['Statistics'].get('DataScannedInBytes',0)/1e6:.0f} MB)")
    if st != "SUCCEEDED":
        raise RuntimeError(info["Status"].get("StateChangeReason"))
    return qid


def fetch(sql, label):
    qid = run(sql, label)
    obj = s3.get_object(Bucket=ATHENA_BUCKET, Key=f"results/{qid}.csv")
    return pd.read_csv(io.BytesIO(obj["Body"].read()))


# ══ 1. MARKET BASKET / RECOMMENDATIONS (category association rules) ══
# Real co-purchase: customers who bought A also bought B, with lift.
mb = fetch("""
WITH cust_cat AS (SELECT DISTINCT customer_id, category FROM karoo_db.orders_curated),
     totals AS (SELECT COUNT(DISTINCT customer_id) AS n FROM karoo_db.orders_curated),
     cat_n AS (SELECT category, COUNT(DISTINCT customer_id) AS c FROM cust_cat GROUP BY category)
SELECT a.category AS antecedent, b.category AS consequent,
       COUNT(DISTINCT a.customer_id) AS pair_customers,
       ca.c AS a_customers, cb.c AS b_customers, (SELECT n FROM totals) AS total_customers
FROM cust_cat a
JOIN cust_cat b ON a.customer_id = b.customer_id AND a.category < b.category
JOIN cat_n ca ON a.category = ca.category
JOIN cat_n cb ON b.category = cb.category
GROUP BY a.category, b.category, ca.c, cb.c
""", "market_basket")

N = mb["total_customers"].iloc[0]
mb["support"] = mb["pair_customers"] / N
mb["conf_a_to_b"] = mb["pair_customers"] / mb["a_customers"]
mb["lift"] = (mb["pair_customers"] * N) / (mb["a_customers"] * mb["b_customers"])
mb = mb.sort_values("lift", ascending=False)
mb.to_csv(OUT / "recommendations_rules.csv", index=False)
print(f"\nTop category associations by lift:")
print(mb[["antecedent", "consequent", "pair_customers", "conf_a_to_b", "lift"]].head(8).to_string(index=False))

# ══ 2. CORRELATIONS (order-level numeric features) ══
sample = fetch("""
SELECT qty, unit_price, discount_pct, promised_days, actual_days,
       CAST(on_time AS INT) AS on_time, returned, net_revenue,
       CASE WHEN province IN ('Gauteng','Western Cape','KwaZulu-Natal') THEN 1 ELSE 0 END AS is_metro
FROM karoo_db.orders_curated TABLESAMPLE BERNOULLI (2)
""", "correlation_sample")
corr = sample.corr(numeric_only=True).round(3)
corr.to_csv(OUT / "correlation_matrix.csv")
print(f"\nCorrelation sample: {len(sample):,} rows")

# ══ 3. FRAUD DETECTION (customer-level anomaly signals) ══
# Real behavioural aggregates per customer, then IsolationForest + rules.
cust = fetch("""
SELECT customer_id,
       COUNT(*) AS orders,
       ROUND(SUM(net_revenue),2) AS total_spend,
       ROUND(AVG(net_revenue),2) AS avg_order_value,
       MAX(qty) AS max_qty,
       ROUND(AVG(CAST(returned AS DOUBLE)),3) AS return_rate,
       ROUND(AVG(discount_pct),1) AS avg_discount,
       date_diff('day', MIN(order_ts), MAX(order_ts)) AS active_days,
       COUNT(DISTINCT province) AS n_provinces
FROM karoo_db.orders_curated
GROUP BY customer_id
HAVING COUNT(*) >= 2
""", "customer_aggregates")

from sklearn.ensemble import IsolationForest
feats = ["orders", "total_spend", "avg_order_value", "max_qty", "return_rate",
         "avg_discount", "n_provinces"]
cust_s = cust.sample(min(200_000, len(cust)), random_state=42).copy()
X = cust_s[feats].fillna(0)
iso = IsolationForest(n_estimators=100, contamination=0.02, random_state=42, n_jobs=-1)
cust_s["anomaly_score"] = -iso.fit_predict(X)  # 1 = anomaly, -1 -> flip
cust_s["iso_flag"] = (iso.fit_predict(X) == -1).astype(int)

# Interpretable rule flags (fraud typologies)
orders_per_day = cust_s["orders"] / cust_s["active_days"].clip(lower=1)
cust_s["flag_velocity"] = (orders_per_day > 0.5).astype(int)          # rapid ordering
cust_s["flag_return_abuse"] = ((cust_s["return_rate"] > 0.4) & (cust_s["avg_order_value"] > cust_s["avg_order_value"].median())).astype(int)
cust_s["flag_multi_province"] = (cust_s["n_provinces"] >= 4).astype(int)  # shipping to many provinces
cust_s["flag_high_value_outlier"] = (cust_s["avg_order_value"] > cust_s["avg_order_value"].quantile(0.999)).astype(int)
cust_s["risk_flags"] = cust_s[["flag_velocity", "flag_return_abuse", "flag_multi_province", "flag_high_value_outlier"]].sum(axis=1)

fraud_summary = pd.DataFrame({
    "signal": ["ML anomaly (IsolationForest)", "Rapid-order velocity", "Return abuse (wardrobing)",
               "Multi-province shipping", "High-value outlier", "2+ risk flags (review queue)"],
    "customers_flagged": [
        cust_s["iso_flag"].sum(), cust_s["flag_velocity"].sum(), cust_s["flag_return_abuse"].sum(),
        cust_s["flag_multi_province"].sum(), cust_s["flag_high_value_outlier"].sum(),
        (cust_s["risk_flags"] >= 2).sum(),
    ],
})
fraud_summary["pct_of_base"] = (fraud_summary["customers_flagged"] / len(cust_s) * 100).round(2)
fraud_summary.to_csv(OUT / "fraud_signals.csv", index=False)
cust_s.nlargest(200, "risk_flags").to_csv(OUT / "fraud_review_queue.csv", index=False)
print(f"\nFraud analysis on {len(cust_s):,} multi-order customers:")
print(fraud_summary.to_string(index=False))

print("\nAll advanced analytics saved to", OUT)

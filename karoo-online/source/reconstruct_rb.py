"""Rebuild rb_summary.json from the existing behavioural CSVs (avoids
re-running the heavy 1M-row generator; values are identical)."""
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import precision_score, recall_score

OUT = Path(__file__).parent / "out"
corr = pd.read_csv(OUT / "rb_correlation_matrix.csv", index_col=0)
rec = pd.read_csv(OUT / "rb_recommendations.csv").sort_values("lift", ascending=False)
fs = pd.read_csv(OUT / "rb_fraud_summary.csv")
scored = pd.read_csv(OUT / "rb_fraud_scored.csv")

review = fs[fs["signal"].str.contains("Review queue")].iloc[0]
top = rec.iloc[0]
summary = {
    "n_orders": 1015703,
    "n_customers": int(len(scored)),
    "true_fraud": int(scored["is_fraud"].sum()),
    "fraud_pct": round(100 * scored["is_fraud"].mean(), 2),
    "iso_precision": round(precision_score(scored["is_fraud"], scored["iso_flag"]), 3),
    "iso_recall": round(recall_score(scored["is_fraud"], scored["iso_flag"]), 3),
    "corr_discount_qty": float(corr.loc["discount_pct", "qty"]),
    "corr_late_return": float(corr.loc["late", "returned"]),
    "corr_metro_delivery": float(corr.loc["is_metro", "actual_days"]),
    "top_rule": f"{top['antecedent']} + {top['consequent']}",
    "top_lift": float(top["lift"]),
    "review_queue": int(review["flagged"]),
    "review_queue_fraud": int(review["captures_real_fraud"]),
}
json.dump(summary, open(OUT / "rb_summary.json", "w"), indent=2)
print("rb_summary.json rebuilt:")
for k, v in summary.items():
    print(f"  {k}: {v}")

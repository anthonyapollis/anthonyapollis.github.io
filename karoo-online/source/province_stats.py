"""Pull rich per-province stats from the lakehouse for the interactive map
hover: revenue, orders, on-time %, avg delivery days, top category, share."""
import io
import time
from pathlib import Path

import boto3
import pandas as pd

REGION = "eu-north-1"
OUT = Path(__file__).parent / "out"
athena = boto3.client("athena", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)


def fetch(sql):
    qid = athena.start_query_execution(QueryString=sql, WorkGroup="karoo-wg",
                                       QueryExecutionContext={"Database": "karoo_db"})["QueryExecutionId"]
    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]["State"]
        if st in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    if st != "SUCCEEDED":
        raise RuntimeError(st)
    obj = s3.get_object(Bucket="karoo-athena-results-a7227216", Key=f"results/{qid}.csv")
    return pd.read_csv(io.BytesIO(obj["Body"].read()))


stats = fetch("""
SELECT province,
       COUNT(*) AS orders,
       ROUND(SUM(net_revenue), 0) AS revenue,
       ROUND(100.0 * AVG(on_time), 1) AS on_time_pct,
       ROUND(AVG(actual_days), 1) AS avg_delivery_days,
       COUNT(DISTINCT customer_id) AS customers
FROM karoo_db.orders_curated GROUP BY province
""")

topcat = fetch("""
SELECT province, category FROM (
  SELECT province, category, SUM(net_revenue) rev,
         ROW_NUMBER() OVER (PARTITION BY province ORDER BY SUM(net_revenue) DESC) rn
  FROM karoo_db.orders_curated GROUP BY province, category
) WHERE rn = 1
""")

stats = stats.merge(topcat.rename(columns={"category": "top_category"}), on="province")
stats["revenue_share_pct"] = (100 * stats["revenue"] / stats["revenue"].sum()).round(1)
stats = stats.sort_values("revenue", ascending=False)
stats.to_csv(OUT / "province_stats.csv", index=False)
print(stats.to_string(index=False))

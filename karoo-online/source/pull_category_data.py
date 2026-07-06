"""Pull real per-category aggregates from the 10M-row lakehouse to ground
the product allocation in actual data."""
import time
from pathlib import Path

import boto3

REGION = "eu-north-1"
WORKGROUP = "karoo-wg"
ATHENA_BUCKET = "karoo-athena-results-a7227216"
OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

athena = boto3.client("athena", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

QUERIES = {
    "category_totals": """
        SELECT category,
               COUNT(*)                             AS orders,
               SUM(qty)                             AS units,
               ROUND(SUM(net_revenue), 0)           AS revenue,
               ROUND(AVG(unit_price), 2)            AS avg_price,
               ROUND(100.0 * AVG(returned), 2)      AS return_pct,
               ROUND(AVG(actual_days), 2)           AS avg_delivery_days,
               ROUND(100.0 * AVG(on_time), 2)       AS on_time_pct
        FROM karoo_db.orders_curated
        GROUP BY category
        ORDER BY revenue DESC
    """,
    "province_category": """
        SELECT province, category,
               ROUND(SUM(net_revenue), 0) AS revenue
        FROM karoo_db.orders_curated
        GROUP BY province, category
    """,
    "monthly_category": """
        SELECT order_month, category,
               ROUND(SUM(net_revenue), 0) AS revenue
        FROM karoo_db.orders_curated
        GROUP BY order_month, category
    """,
}


def run(sql, label):
    qid = athena.start_query_execution(
        QueryString=sql, WorkGroup=WORKGROUP,
        QueryExecutionContext={"Database": "karoo_db"},
    )["QueryExecutionId"]
    while True:
        info = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        st = info["Status"]["State"]
        if st in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    print(f"[{label}] {st}  ({info['Statistics'].get('DataScannedInBytes',0)/1e6:.0f} MB)")
    if st != "SUCCEEDED":
        raise RuntimeError(info["Status"].get("StateChangeReason"))
    return qid


for name, sql in QUERIES.items():
    qid = run(sql, name)
    s3.download_file(ATHENA_BUCKET, f"results/{qid}.csv", str(OUT / f"{name}.csv"))
    print(f"    -> {name}.csv")

print("Done.")

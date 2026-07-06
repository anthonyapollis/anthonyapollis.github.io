import pandas as pd
from pathlib import Path

folder = Path(r"C:\Users\Anthony.DESKTOP-ES5HL78\Downloads\takealot_product_extraction")
for f in ["takealot_product_details_1000.xlsx", "takealot_product_details_sample.xlsx"]:
    p = folder / f
    if p.exists():
        df = pd.read_excel(p)
        print(f"\n===== {f} =====")
        print("rows:", len(df), "cols:", list(df.columns))
        print(df.head(3).to_string())
        break

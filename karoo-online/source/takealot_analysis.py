"""Analyse the REAL scraped Takealot product data (1000 products).
Clean prices/brands/availability, classify products into categories from
their titles, and produce the product-level tables for the data story."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(r"C:\Users\Anthony.DESKTOP-ES5HL78\Downloads\takealot_product_extraction\takealot_product_details_1000.csv")
OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC)
print(f"Loaded {len(df)} real Takealot products")
print("Columns:", list(df.columns))

# ── Clean ──
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["brand"] = df["brand"].fillna("").str.strip()
df["title"] = df["title"].fillna("").str.strip()
df["n_images"] = df["image_urls"].fillna("").apply(lambda s: len([u for u in str(s).split("|") if u]))
df["desc_len"] = df["description"].fillna("").str.len()

# availability buckets
def avail_bucket(a):
    a = str(a).lower()
    if "in stock" in a or "ships in 1 -" in a or "same day" in a:
        return "In stock (fast)"
    if re.search(r"ships in \d+ - \d+ work", a):
        return "Lead time (imported)"
    if "no" in a or a in ("nan", ""):
        return "No live offer"
    return "Other"
df["availability_bucket"] = df["availability"].apply(avail_bucket)

# ── Category classification from title keywords ──
CATEGORY_KEYWORDS = {
    "Electronics": ["phone", "laptop", "tablet", "charger", "cable", "usb", "bluetooth", "speaker",
                    "headphone", "earbud", "tv", "monitor", "camera", "power bank", "mouse", "keyboard",
                    "ssd", "hard drive", "router", "adapter", "hdmi", "smartwatch", "gaming"],
    "Home & Kitchen": ["kitchen", "pot", "pan", "knife", "cookware", "kettle", "toaster", "blender",
                       "mixer", "fryer", "vacuum", "iron", "cushion", "bedding", "duvet", "towel",
                       "curtain", "storage", "organizer", "cup", "mug", "plate", "bowl", "bottle",
                       "lamp", "light", "decor", "furniture", "chair", "table", "shelf"],
    "Beauty & Health": ["cream", "serum", "lotion", "shampoo", "hair", "makeup", "lipstick", "perfume",
                        "skincare", "nail", "beard", "shaver", "trimmer", "massage", "vitamin",
                        "supplement", "toothbrush", "soap"],
    "Toys & Games": ["toy", "game", "puzzle", "lego", "block", "doll", "figure", "playset", "board game",
                     "card game", "rc ", "remote control", "kids", "children"],
    "Sport & Outdoor": ["fitness", "gym", "yoga", "dumbbell", "weight", "bike", "cycling", "tent",
                        "camping", "hiking", "backpack", "running", "sport", "ball", "fishing", "cooler"],
    "Fashion": ["shirt", "dress", "jeans", "jacket", "shoe", "sneaker", "boot", "sandal", "watch",
                "bag", "wallet", "belt", "hat", "cap", "sunglasses", "scarf", "sock"],
    "Baby & Kids": ["baby", "infant", "nappy", "diaper", "stroller", "pram", "cot", "feeding",
                    "pacifier", "bib"],
    "Automotive": ["car ", "auto", "vehicle", "tyre", "tire", "engine", "motor", "wiper", "dash cam",
                   "jump starter"],
    "Tools & DIY": ["drill", "tool", "screwdriver", "hammer", "saw", "wrench", "sander", "grinder",
                    "welding", "ladder", "torch", "tape measure"],
    "Stationery & Office": ["pen", "notebook", "paper", "stapler", "printer", "ink", "desk", "file",
                            "folder", "marker", "calculator", "magnifying", "magnifier"],
    "Pet Supplies": ["dog", "cat", "pet", "aquarium", "fish tank", "bird", "leash", "kennel"],
}

def classify(title):
    t = title.lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in kws if kw in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General Merchandise"

df["category"] = df["title"].apply(classify)

# ── Save cleaned master ──
keep = ["sku_or_id", "title", "brand", "category", "price", "availability",
        "availability_bucket", "n_images", "desc_len", "source_url", "image_url"]
clean = df[keep].copy()
clean.to_csv(OUT / "takealot_products_clean.csv", index=False)

# ── Analyses ──
priced = clean[clean["price"].notna() & (clean["price"] > 0)]

# Top / bottom by price
top_price = priced.nlargest(10, "price")[["title", "brand", "category", "price", "availability_bucket"]]
bottom_price = priced.nsmallest(10, "price")[["title", "brand", "category", "price", "availability_bucket"]]
top_price.to_csv(OUT / "tk_top10_price.csv", index=False)
bottom_price.to_csv(OUT / "tk_bottom10_price.csv", index=False)

# Category summary
cat_sum = clean.groupby("category").agg(
    products=("sku_or_id", "count"),
    priced=("price", lambda s: s.notna().sum()),
    median_price=("price", "median"),
    avg_price=("price", "mean"),
    avg_images=("n_images", "mean"),
    avg_desc_len=("desc_len", "mean"),
).round(1).sort_values("products", ascending=False).reset_index()
cat_sum.to_csv(OUT / "tk_category_summary.csv", index=False)

# Brand summary (only real brands)
branded = clean[clean["brand"] != ""]
brand_sum = branded.groupby("brand").agg(
    products=("sku_or_id", "count"),
    median_price=("price", "median"),
    categories=("category", "nunique"),
).sort_values("products", ascending=False).head(20).reset_index()
brand_sum.to_csv(OUT / "tk_brand_summary.csv", index=False)

# Availability summary
avail_sum = clean.groupby("availability_bucket").agg(
    products=("sku_or_id", "count"),
    median_price=("price", "median"),
).sort_values("products", ascending=False).reset_index()
avail_sum.to_csv(OUT / "tk_availability.csv", index=False)

# ── Print report ──
print(f"\nPriced products: {len(priced)}/{len(clean)} ({100*len(priced)/len(clean):.0f}%)")
print(f"Price range: R{priced['price'].min():.0f} - R{priced['price'].max():,.0f}, "
      f"median R{priced['price'].median():.0f}, mean R{priced['price'].mean():,.0f}")
print(f"Branded products: {len(branded)}/{len(clean)} ({100*len(branded)/len(clean):.0f}%)")
print(f"Avg images/product: {clean['n_images'].mean():.1f}")
print(f"Products with description: {(clean['desc_len']>0).sum()} ({100*(clean['desc_len']>0).mean():.0f}%)")

print("\nCategories:")
print(cat_sum.to_string(index=False))
print("\nAvailability:")
print(avail_sum.to_string(index=False))
print("\nMost expensive real products:")
print(top_price.head().to_string(index=False))

# summary json for the report
import json
summary = {
    "n_products": len(clean),
    "n_priced": len(priced),
    "pct_priced": round(100*len(priced)/len(clean)),
    "price_min": round(priced["price"].min()),
    "price_max": round(priced["price"].max()),
    "price_median": round(priced["price"].median()),
    "price_mean": round(priced["price"].mean()),
    "n_branded": len(branded),
    "pct_branded": round(100*len(branded)/len(clean)),
    "n_brands": branded["brand"].nunique(),
    "avg_images": round(clean["n_images"].mean(), 1),
    "pct_desc": round(100*(clean["desc_len"]>0).mean()),
    "n_categories": clean["category"].nunique(),
    "top_category": cat_sum.iloc[0]["category"],
    "pct_in_stock": round(100*(clean["availability_bucket"]=="In stock (fast)").mean()),
    "pct_lead_time": round(100*(clean["availability_bucket"]=="Lead time (imported)").mean()),
    "pct_no_offer": round(100*(clean["availability_bucket"]=="No live offer").mean()),
}
json.dump(summary, open(OUT / "tk_summary.json", "w"), indent=2)
print("\nSaved all Takealot analysis to", OUT)

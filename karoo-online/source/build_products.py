"""Build a realistic Karoo product catalog + brands, then allocate the REAL
category-level sales (from the 10M-row lakehouse) across products using a
Pareto distribution. Everything ties back to the true category totals."""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "out"
rng = np.random.default_rng(42)

cat_totals = pd.read_csv(OUT / "category_totals.csv")

# ── Product catalog: (category, product_name, brand, tier) ──
# Tier drives price relative to category avg: budget 0.5x, mid 1.0x, premium 2.2x
CATALOG = {
    "Electronics": [
        ("55\" 4K Smart TV", "Vortex", "premium"), ("Wireless Earbuds Pro", "SonicWave", "mid"),
        ("Bluetooth Speaker", "SonicWave", "mid"), ("Laptop 15\" i5", "Vortex", "premium"),
        ("Power Bank 20000mAh", "Voltiq", "budget"), ("Smartphone A54", "Nexa", "premium"),
        ("Smartwatch Fit", "Nexa", "mid"), ("USB-C Charger", "Voltiq", "budget"),
        ("Gaming Mouse", "Raptor", "mid"), ("Soundbar 2.1", "SonicWave", "premium"),
    ],
    "Garden & Pool": [
        ("Pool Cleaning Kit", "AquaLife", "mid"), ("Patio Umbrella 3m", "Veld", "mid"),
        ("Braai Stand Deluxe", "Kaya", "premium"), ("Garden Hose 30m", "GreenThumb", "budget"),
        ("Solar Pool Heater", "AquaLife", "premium"), ("Lawn Mower Electric", "Veld", "premium"),
        ("Pool Float Set", "AquaLife", "budget"), ("Plant Pot Trio", "GreenThumb", "budget"),
        ("Gazebo 3x3m", "Kaya", "premium"), ("Garden Tool Set", "GreenThumb", "mid"),
    ],
    "Sport & Outdoor": [
        ("Mountain Bike 29\"", "Trailblaze", "premium"), ("Camping Tent 4-Man", "Veld", "mid"),
        ("Yoga Mat Pro", "FlexFit", "budget"), ("Dumbbell Set 20kg", "IronCore", "mid"),
        ("Running Shoes Trail", "Stride", "mid"), ("Hiking Backpack 60L", "Veld", "premium"),
        ("Sleeping Bag -5°C", "Veld", "mid"), ("Football Match Ball", "Stride", "budget"),
        ("Fitness Tracker Band", "FlexFit", "mid"), ("Cooler Box 50L", "Kaya", "mid"),
    ],
    "Automotive": [
        ("Car Battery 12V", "TorqueX", "mid"), ("Dash Cam Full HD", "Voltiq", "mid"),
        ("Tyre Inflator", "TorqueX", "budget"), ("Car Seat Cover Set", "DriveLux", "mid"),
        ("Engine Oil 5W-40 5L", "TorqueX", "budget"), ("Jump Starter Kit", "Voltiq", "premium"),
        ("Roof Rack System", "DriveLux", "premium"), ("Car Vacuum Cleaner", "TorqueX", "budget"),
        ("LED Headlight Kit", "Voltiq", "mid"), ("Windscreen Sun Shade", "DriveLux", "budget"),
    ],
    "Home & Kitchen": [
        ("Air Fryer 5.5L", "ChefPro", "mid"), ("Coffee Machine", "ChefPro", "premium"),
        ("Non-Stick Pan Set", "Hearth", "mid"), ("Stand Mixer", "ChefPro", "premium"),
        ("Cutlery Set 24pc", "Hearth", "budget"), ("Vacuum Cleaner Bagless", "Hearth", "premium"),
        ("Kettle 1.7L", "ChefPro", "budget"), ("Dinner Set 16pc", "Hearth", "mid"),
        ("Blender 1000W", "ChefPro", "mid"), ("Storage Container Set", "Hearth", "budget"),
    ],
    "Baby": [
        ("Baby Stroller 3-in-1", "LittleOnes", "premium"), ("Car Seat Group 1-3", "LittleOnes", "premium"),
        ("Nappy Mega Pack", "TenderCare", "budget"), ("Baby Monitor Video", "TenderCare", "mid"),
        ("Cot Bed Convertible", "LittleOnes", "premium"), ("Feeding Bottle Set", "TenderCare", "budget"),
        ("Baby Carrier Ergo", "LittleOnes", "mid"), ("Playmat Activity Gym", "TinyTots", "mid"),
        ("Baby Bath Set", "TinyTots", "budget"), ("Highchair Foldable", "TinyTots", "mid"),
    ],
    "Toys": [
        ("Building Blocks 500pc", "PlayLand", "mid"), ("Remote Control Car", "SpeedToy", "mid"),
        ("Doll House Deluxe", "PlayLand", "premium"), ("Board Game Classic", "FunBox", "budget"),
        ("Puzzle 1000pc", "FunBox", "budget"), ("Action Figure Set", "SpeedToy", "mid"),
        ("Kids Scooter 3-Wheel", "SpeedToy", "mid"), ("Plush Teddy XL", "PlayLand", "budget"),
        ("STEM Robot Kit", "PlayLand", "premium"), ("Art & Craft Kit", "FunBox", "budget"),
    ],
    "Fashion": [
        ("Leather Jacket", "Kalahari Co.", "premium"), ("Running Sneakers", "Stride", "mid"),
        ("Denim Jeans Slim", "Kalahari Co.", "mid"), ("Summer Dress Floral", "Bloom", "mid"),
        ("Cotton T-Shirt 3pk", "Everyday", "budget"), ("Winter Coat Puffer", "Kalahari Co.", "premium"),
        ("Handbag Tote", "Bloom", "premium"), ("Sports Cap", "Everyday", "budget"),
        ("Sandals Leather", "Bloom", "mid"), ("Formal Shirt", "Everyday", "mid"),
    ],
    "Pet Supplies": [
        ("Dog Food 15kg", "PawNutrition", "mid"), ("Cat Scratching Tower", "Whiskers", "mid"),
        ("Pet Bed Large", "PawNutrition", "budget"), ("Aquarium Kit 60L", "Whiskers", "premium"),
        ("Dog Leash & Collar", "PawNutrition", "budget"), ("Cat Litter 10kg", "Whiskers", "budget"),
        ("Pet Carrier", "PawNutrition", "mid"), ("Chew Toy Bundle", "Whiskers", "budget"),
        ("Automatic Feeder", "PawNutrition", "premium"), ("Fish Tank Filter", "Whiskers", "mid"),
    ],
    "Beauty": [
        ("Perfume Eau de Parfum", "Lumière", "premium"), ("Skincare Gift Set", "Lumière", "mid"),
        ("Hair Dryer Ionic", "GlowUp", "mid"), ("Makeup Palette", "GlowUp", "mid"),
        ("Electric Shaver", "GroomKing", "mid"), ("Face Serum Vitamin C", "Lumière", "budget"),
        ("Hair Straightener", "GlowUp", "premium"), ("Beard Trimmer Kit", "GroomKing", "budget"),
        ("Nail Care Set", "GlowUp", "budget"), ("Body Lotion Set", "Lumière", "budget"),
    ],
    "Books": [
        ("SA Bestseller Novel", "Cape Press", "budget"), ("Cookbook Braai Edition", "Cape Press", "mid"),
        ("Kids Story Collection", "Little Reader", "budget"), ("Business Strategy Book", "Cape Press", "mid"),
        ("Self-Help Guide", "Mindful", "budget"), ("Coffee Table Photo Book", "Cape Press", "premium"),
        ("Study Guide Matric", "Little Reader", "budget"), ("Biography Bestseller", "Cape Press", "mid"),
        ("Colouring Book Adult", "Mindful", "budget"), ("Travel Guide SA", "Cape Press", "budget"),
    ],
    "Groceries": [
        ("Rooibos Tea 80s", "Karoo Pantry", "budget"), ("Biltong 1kg", "Karoo Pantry", "premium"),
        ("Coffee Beans 1kg", "Bean Co.", "mid"), ("Olive Oil 750ml", "Karoo Pantry", "mid"),
        ("Snack Box Variety", "Bean Co.", "budget"), ("Chocolate Gift Hamper", "Karoo Pantry", "premium"),
        ("Pasta Selection 6pk", "Bean Co.", "budget"), ("Rusks 1kg", "Karoo Pantry", "budget"),
        ("Craft Sauce Trio", "Bean Co.", "mid"), ("Nuts & Dried Fruit 2kg", "Karoo Pantry", "mid"),
    ],
}

TIER_MULT = {"budget": 0.5, "mid": 1.0, "premium": 2.2}

rows = []
pid = 1000
for _, cat in cat_totals.iterrows():
    name = cat["category"]
    prods = CATALOG[name]
    n = len(prods)
    # Pareto allocation of units: a few winners dominate
    weights = rng.pareto(1.4, n) + 0.15
    weights = np.sort(weights)[::-1]  # biggest first, then shuffle to product order
    rng.shuffle(weights)
    weights = weights / weights.sum()
    cat_revenue = float(cat["revenue"])
    cat_avg_price = cat["avg_price"]
    cat_return = cat["return_pct"]

    for (pname, brand, tier), wt in zip(prods, weights):
        pid += 1
        price = round(cat_avg_price * TIER_MULT[tier] * rng.uniform(0.85, 1.15), 2)
        # discount averages ~7% (matches generator); premium discounts less
        disc = rng.uniform(0.02, 0.10) * (0.6 if tier == "premium" else 1.0)
        # allocate REAL category revenue by Pareto weight -> revenue ties out exactly
        revenue = round(cat_revenue * wt, 0)
        units = int(revenue / (price * (1 - disc)))
        # return rate varies around category mean; premium returns a bit less
        ret = max(0.3, rng.normal(cat_return, cat_return * 0.25) * (0.8 if tier == "premium" else 1.0))
        # rating: higher for premium & low-return, plus noise, clamped 3.2-4.9
        rating = np.clip(4.7 - ret * 0.05 + (0.2 if tier == "premium" else 0) + rng.normal(0, 0.15), 3.2, 4.9)
        rows.append({
            "product_id": f"KP{pid}", "product_name": pname, "brand": brand,
            "category": name, "tier": tier, "unit_price": price,
            "units_sold": units, "revenue": revenue,
            "return_pct": round(ret, 2), "avg_rating": round(rating, 1),
            "discount_pct": round(disc * 100, 1),
        })

products = pd.DataFrame(rows)
products = products.sort_values("revenue", ascending=False).reset_index(drop=True)
products.to_csv(OUT / "products_master.csv", index=False)

# ── Aggregations for the story ──
brands = products.groupby("brand").agg(
    products=("product_id", "count"), category=("category", "first"),
    units_sold=("units_sold", "sum"), revenue=("revenue", "sum"),
    avg_rating=("avg_rating", "mean"), avg_return_pct=("return_pct", "mean"),
).round(2).sort_values("revenue", ascending=False).reset_index()
brands.to_csv(OUT / "brands.csv", index=False)

cat_summary = products.groupby("category").agg(
    products=("product_id", "count"), units_sold=("units_sold", "sum"),
    revenue=("revenue", "sum"), avg_rating=("avg_rating", "mean"),
    avg_return_pct=("return_pct", "mean"),
).round(2).sort_values("revenue", ascending=False).reset_index()
cat_summary.to_csv(OUT / "category_summary.csv", index=False)

print(f"Products: {len(products)}, Brands: {len(brands)}, Categories: {len(cat_summary)}")
print(f"Total allocated revenue: R{products['revenue'].sum()/1e9:.2f}bn "
      f"(actual lakehouse: R{cat_totals['revenue'].astype(float).sum()/1e9:.2f}bn)")
print("\nTop 5 products:")
print(products[["product_name", "brand", "category", "revenue", "avg_rating"]].head().to_string(index=False))
print("\nWorst 5 products by revenue:")
print(products[["product_name", "brand", "category", "revenue", "avg_rating"]].tail().to_string(index=False))

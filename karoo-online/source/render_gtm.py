"""Render a clean two-panel GTM demonstration visual (storefront funnel +
the dataLayer events it fires) from the real captured event sequence."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "out" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0",
     "cream": "#FBF3EC", "gold": "#E0A526", "sage": "#6B8E5A"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.4), gridspec_kw={"width_ratios": [1, 1.15]})

# ── Panel 1: storefront funnel (mock) ──
ax1.set_xlim(0, 10); ax1.set_ylim(0, 10); ax1.axis("off")
ax1.add_patch(FancyBboxPatch((0.2, 9.0), 9.6, 0.9, boxstyle="round,pad=0.02,rounding_size=0.08",
              fc=K["ink"], ec="none"))
ax1.text(0.5, 9.45, "KAROO ONLINE", fontsize=13, fontweight="bold", color=K["gold"], va="center")
ax1.text(0.5, 9.05, "Google Tag Manager — tracking demo storefront", fontsize=7.5, color="#C9BBA8", va="center")

steps = [("1 · Product View", "view_item", K["sage"], "✓ fired"),
         ("2 · Add to Cart", "add_to_cart", K["sage"], "✓ fired"),
         ("3 · Begin Checkout", "begin_checkout", K["sage"], "✓ fired"),
         ("4 · Purchase  (R899)", "purchase", K["ochre"], "✓ fired")]
y = 7.6
for title, ev, col, status in steps:
    ax1.add_patch(FancyBboxPatch((0.4, y-0.05), 9.2, 1.35, boxstyle="round,pad=0.02,rounding_size=0.1",
                  fc="white", ec=col, lw=2))
    ax1.text(0.8, y+0.85, title, fontsize=11, fontweight="bold", color=K["ochre"], va="center")
    ax1.add_patch(FancyBboxPatch((0.8, y+0.15), 2.5, 0.42, boxstyle="round,pad=0.02,rounding_size=0.1",
                  fc=K["cream"], ec="none"))
    ax1.text(0.95, y+0.36, ev, fontsize=9, color=K["clay"], va="center", family="monospace")
    ax1.text(8.9, y+0.55, status, fontsize=9.5, color=K["sage"], va="center", ha="right", fontweight="bold")
    y -= 1.75
ax1.set_title("The storefront (GTM installed)", fontsize=12, fontweight="bold", color=K["ink"], pad=8)

# ── Panel 2: dataLayer events fired (dark console) ──
ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
ax2.add_patch(FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.02,rounding_size=0.12",
              fc="#1E1611", ec=K["clay"], lw=1.5))
events = [
    ("session_start", '{ session_id: "sess_a3f9k2" }'),
    ("page_view", '{ page_path: "/product/cordless-drill" }'),
    ("view_item", '{ items: [{ id:"SKU-1042", cat:"Electronics" }] }'),
    ("add_to_cart", '{ value: 899, currency: "ZAR" }'),
    ("begin_checkout", '{ value: 899, currency: "ZAR" }'),
    ("purchase", '{ transaction_id:"T62800", value:899, currency:"ZAR" }'),
]
ax2.text(0.5, 9.5, "dataLayer  —  events GTM captures & forwards to GA4", fontsize=10,
         color=K["gold"], fontweight="bold", va="center", family="monospace")
yy = 8.7
for ev, payload in events:
    ax2.text(0.5, yy, "dataLayer.push", fontsize=9.5, color=K["gold"], va="top", family="monospace")
    ax2.text(2.9, yy, f'{{ event: "{ev}",', fontsize=9.5, color="#F5E9DC", va="top", family="monospace")
    ax2.text(0.9, yy-0.42, payload, fontsize=8.3, color="#c9bba8", va="top", family="monospace")
    ax2.text(0.9, yy-0.78, "}", fontsize=9.5, color="#F5E9DC", va="top", family="monospace")
    yy -= 1.4
ax2.set_title("→ every action fires a tracked event", fontsize=12, fontweight="bold", color=K["ink"], pad=8)

fig.suptitle("Google Tag Manager in action — how Karoo Online captures on-site behaviour",
             fontsize=15, fontweight="bold", color=K["ink"], y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT / "gtm_demo.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Rendered gtm_demo.png")

"""Render realistic browser-mockup 'screenshots' of the GTM demo in action —
a storefront window firing events, and a DevTools dataLayer view."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

OUT = Path(__file__).parent / "out" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0",
     "cream": "#FBF3EC", "gold": "#E0A526", "sage": "#6B8E5A", "green": "#4C7A4C"}


def browser_frame(ax, url):
    ax.add_patch(FancyBboxPatch((1, 1), 98, 98, boxstyle="round,pad=0,rounding_size=1.5",
                 fc="white", ec="#c9c9c9", lw=1.5, zorder=1))
    ax.add_patch(Rectangle((1, 92), 98, 7, fc="#f0f0f0", ec="none", zorder=2))
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        ax.add_patch(Circle((5 + i*2.6, 95.5), 0.8, fc=c, ec="none", zorder=3))
    ax.add_patch(FancyBboxPatch((14, 93.6), 78, 3.8, boxstyle="round,pad=0,rounding_size=1",
                 fc="white", ec="#d5d5d5", lw=1, zorder=3))
    ax.text(18, 95.5, url, fontsize=8, va="center", color="#555", zorder=4, family="monospace")


# SHOT 1
fig, ax = plt.subplots(figsize=(7.2, 5.2)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
browser_frame(ax, "karoo-online.co.za/product/cordless-drill")
ax.add_patch(Rectangle((1, 82), 98, 9, fc=K["ink"], ec="none", zorder=2))
ax.text(5, 86.5, "KAROO ONLINE", fontsize=12, color=K["gold"], fontweight="bold", va="center", zorder=3)
ax.text(90, 86.5, "Cart: 1", fontsize=10, color="white", va="center", ha="right", zorder=3)
ax.add_patch(FancyBboxPatch((5, 40), 90, 38, boxstyle="round,pad=0,rounding_size=2", fc="#fafafa", ec="#e5e5e5", lw=1, zorder=2))
ax.add_patch(FancyBboxPatch((8, 45), 30, 28, boxstyle="round,pad=0,rounding_size=1.5", fc=K["cream"], ec="#e0d5c5", lw=1, zorder=3))
ax.text(23, 59, "[  drill  ]", fontsize=13, ha="center", va="center", color=K["clay"], zorder=4)
ax.text(43, 70, "Cordless Drill", fontsize=15, fontweight="bold", color=K["ink"], va="center", zorder=3)
ax.text(43, 64, "Electronics - SKU-1042", fontsize=9, color="#888", va="center", zorder=3)
ax.text(43, 57, "R 899.00", fontsize=18, fontweight="bold", color=K["ochre"], va="center", zorder=3)
ax.text(43, 50, "4.3 stars  -  In stock", fontsize=9, color=K["sage"], va="center", zorder=3)
ax.add_patch(FancyBboxPatch((43, 42.5), 24, 5.5, boxstyle="round,pad=0,rounding_size=1", fc=K["ochre"], ec="none", zorder=3))
ax.text(55, 45.3, "Added to Cart", fontsize=11, color="white", fontweight="bold", ha="center", va="center", zorder=4)
ax.add_patch(FancyBboxPatch((5, 30), 90, 7, boxstyle="round,pad=0,rounding_size=1.2", fc="#1E1611", ec=K["gold"], lw=1.5, zorder=3))
ax.text(8, 33.5, "GTM >", fontsize=9, color=K["gold"], fontweight="bold", va="center", zorder=4, family="monospace")
ax.text(19, 33.5, "dataLayer.push({ event:'add_to_cart', value:899, currency:'ZAR' })", fontsize=7.5, color="#F5E9DC", va="center", zorder=4, family="monospace")
ax.text(50, 24, "The tag fires the instant the shopper clicks - no code change needed.", fontsize=8.5, style="italic", color=K["clay"], ha="center", zorder=3)
ax.text(50, 5, "Storefront with Google Tag Manager installed", fontsize=10, fontweight="bold", color=K["ink"], ha="center", zorder=3)
fig.savefig(OUT / "gtm_shot1.png", dpi=155, bbox_inches="tight", facecolor="white"); plt.close(fig)

# SHOT 2
fig, ax = plt.subplots(figsize=(7.2, 5.2)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
browser_frame(ax, "Tag Assistant - dataLayer inspector")
ax.add_patch(FancyBboxPatch((4, 6), 92, 84, boxstyle="round,pad=0,rounding_size=1.2", fc="#1E1611", ec="#3a2f26", lw=1, zorder=2))
ax.text(7, 86, "> dataLayer", fontsize=10, color=K["gold"], fontweight="bold", va="center", zorder=3, family="monospace")
ax.text(93, 86, "6 events  -  GA4 connected", fontsize=8, color=K["green"], va="center", ha="right", zorder=3, family="monospace")
events = [("session_start", "sess_a3f9k2", K["sage"]), ("page_view", "/product/cordless-drill", K["sage"]),
          ("view_item", "SKU-1042 - Electronics", K["gold"]), ("add_to_cart", "value: 899 - ZAR", K["gold"]),
          ("begin_checkout", "value: 899 - ZAR", K["gold"]), ("purchase", "T62800 - value:899 - ZAR", K["ochre"])]
y = 78
for ev, payload, col in events:
    ax.add_patch(Circle((9, y+0.6), 0.7, fc=col, ec="none", zorder=4))
    ax.text(12, y+0.6, ev, fontsize=9.5, color="#F5E9DC", va="center", zorder=4, family="monospace", fontweight="bold")
    ax.text(42, y+0.6, "->  " + payload, fontsize=8.3, color="#c9bba8", va="center", zorder=4, family="monospace")
    ax.text(93, y+0.6, "sent", fontsize=8, color=K["green"], va="center", ha="right", zorder=4, family="monospace")
    y -= 11.5
ax.text(50, 5, "Every event captured, validated and forwarded to GA4 -> the lakehouse", fontsize=10, fontweight="bold", color=K["ink"], ha="center", zorder=3)
fig.savefig(OUT / "gtm_shot2.png", dpi=155, bbox_inches="tight", facecolor="white"); plt.close(fig)
print("Rendered gtm_shot1.png + gtm_shot2.png")

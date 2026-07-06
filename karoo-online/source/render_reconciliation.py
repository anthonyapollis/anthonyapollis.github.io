"""Render the data-reconciliation visual: how one figure ties out end-to-end,
the validation gates that enforce it, and the tech that makes it possible."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).parent / "out" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0",
     "cream": "#FBF3EC", "gold": "#E0A526", "sage": "#6B8E5A", "teal": "#2A7F7F", "green": "#4C7A4C"}

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), gridspec_kw={"height_ratios": [1, 1]})

# ── TOP: the reconciliation chain — R899 ties out at every hop ──
ax1.set_xlim(0, 14); ax1.set_ylim(0, 5); ax1.axis("off")
ax1.text(7, 4.6, "How one figure reconciles — the R899 sale, traced end-to-end",
         ha="center", fontsize=14, fontweight="bold", color=K["ink"])
stages = [
    ("1 · CAPTURE", "GTM dataLayer\npurchase event", "R899", K["ochre"]),
    ("2 · COLLECT", "GA4 / app\nsession stream", "R899", K["teal"]),
    ("3 · LAND", "S3 raw zone\n(immutable)", "R899", K["clay"]),
    ("4 · TRANSFORM", "Athena CTAS →\ncurated Parquet", "R899", K["gold"]),
    ("5 · REPORT", "KPI in this\nreport", "R899", K["green"]),
]
w = 2.15; gap = 0.45; x = 0.3
for i, (stage, desc, val, col) in enumerate(stages):
    ax1.add_patch(FancyBboxPatch((x, 1.4), w, 2.2, boxstyle="round,pad=0.03,rounding_size=0.12",
                  fc="white", ec=col, lw=2.2))
    ax1.text(x + w/2, 3.3, stage, ha="center", fontsize=8.5, fontweight="bold", color=col)
    ax1.text(x + w/2, 2.65, desc, ha="center", fontsize=8, color=K["ink"])
    ax1.add_patch(FancyBboxPatch((x + w/2 - 0.55, 1.6), 1.1, 0.55,
                  boxstyle="round,pad=0.02,rounding_size=0.1", fc=col, ec="none"))
    ax1.text(x + w/2, 1.87, val, ha="center", va="center", fontsize=11, fontweight="bold", color="white")
    if i < len(stages) - 1:
        ax1.add_patch(FancyArrowPatch((x + w, 2.5), (x + w + gap, 2.5), arrowstyle="-|>",
                      mutation_scale=15, lw=1.8, color=K["clay"]))
        ax1.text(x + w + gap/2, 2.85, "=", ha="center", fontsize=13, fontweight="bold", color=K["green"])
    x += w + gap
ax1.text(7, 0.75, "Because every stage reads the SAME governed value, the number never drifts — "
         "revenue in the report equals revenue at the checkout.",
         ha="center", fontsize=9.5, style="italic", color=K["clay"])

# ── BOTTOM: validation gates + tech enablers ──
ax2.set_xlim(0, 14); ax2.set_ylim(0, 5); ax2.axis("off")

# Left: validation gates
ax2.text(3.3, 4.6, "Validation gates (run before any figure is trusted)",
         ha="center", fontsize=11.5, fontweight="bold", color=K["ochre"])
gates = [
    "Null-rate checks on every join key",
    "Duplicate detection (1 install = 1 row)",
    "Referential integrity — 100% of IDs resolve",
    "Cost-invariant (spend only on valid rows)",
    "Revenue totals cross-checked source ↔ report",
]
for i, g in enumerate(gates):
    y = 3.9 - i * 0.62
    ax2.add_patch(FancyBboxPatch((0.3, y - 0.22), 6, 0.5, boxstyle="round,pad=0.02,rounding_size=0.1",
                  fc=K["cream"], ec=K["sand"], lw=1))
    ax2.text(0.6, y + 0.03, "✓", fontsize=12, color=K["green"], fontweight="bold", va="center")
    ax2.text(1.1, y + 0.03, g, fontsize=9, color=K["ink"], va="center")

# Right: tech enablers
ax2.text(10.5, 4.6, "The tech that makes it possible",
         ha="center", fontsize=11.5, fontweight="bold", color=K["teal"])
tech = [
    ("One catalogue (AWS Glue)", "every tool reads the same schema"),
    ("Immutable raw zone (S3)", "the source of truth never changes"),
    ("Deterministic ETL (Athena CTAS)", "same input → same output, every run"),
    ("Partitioned Parquet", "consistent, cheap, repeatable queries"),
    ("Infrastructure as code (Terraform)", "the whole pipeline is reproducible"),
]
for i, (t, d) in enumerate(tech):
    y = 3.9 - i * 0.62
    ax2.add_patch(FancyBboxPatch((7.3, y - 0.22), 6.4, 0.5, boxstyle="round,pad=0.02,rounding_size=0.1",
                  fc="white", ec=K["teal"], lw=1.2))
    ax2.text(7.6, y + 0.03, t, fontsize=9, color=K["ink"], va="center", fontweight="bold")
    ax2.text(7.6, y - 0.16, d, fontsize=7.3, color=K["clay"], va="center")

fig.tight_layout(pad=1.5)
fig.savefig(OUT / "reconciliation.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Rendered reconciliation.png")

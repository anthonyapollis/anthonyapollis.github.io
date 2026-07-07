"""Render the guided ML-journey visuals: (1) the 5-step journey framework
every model follows, and (2) a model scorecard grading the four models."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).parent / "out"
CHARTS = OUT / "charts"
rb = json.load(open(OUT / "rb_summary.json"))
lc = json.load(open(OUT / "lifecycle_summary.json"))
K = {"ochre": "#C0531F", "clay": "#7A4A2B", "ink": "#2B2118", "sand": "#E8D5C0", "cream": "#FBF3EC",
     "teal": "#2A7F7F", "gold": "#E0A526", "sage": "#6B8E5A", "green": "#4C7A4C", "plum": "#7D5BA6", "rust": "#A5361A"}

# ══ 1. The ML journey framework ══
fig, ax = plt.subplots(figsize=(13, 3.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.axis("off")
ax.text(50, 28, "Every model follows the same journey — from a business question to a decision",
        ha="center", fontsize=13, fontweight="bold", color=K["ink"])
steps = [
    ("1  ASK", "a business\nquestion", K["ochre"]),
    ("2  PREPARE", "features from the\ncurated lakehouse", K["teal"]),
    ("3  TRAIN", "test several models,\nkeep the best", K["gold"]),
    ("4  VALIDATE", "honest metrics vs\na naive baseline", K["sage"]),
    ("5  DECIDE", "ship the action\nit unlocks", K["green"]),
]
w = 15.4; gap = 3.5; x = 4.4
for i, (t, d, c) in enumerate(steps):
    ax.add_patch(FancyBboxPatch((x, 6), w, 15, boxstyle="round,pad=0.3,rounding_size=1.2",
                 fc="white", ec=c, lw=2.4))
    ax.text(x + w/2, 17, t, ha="center", fontsize=11, fontweight="bold", color=c)
    ax.text(x + w/2, 10.5, d, ha="center", fontsize=8.5, color=K["ink"])
    if i < len(steps) - 1:
        ax.add_patch(FancyArrowPatch((x + w, 13.5), (x + w + gap, 13.5), arrowstyle="-|>",
                     mutation_scale=17, lw=2, color=K["clay"]))
    x += w + gap
ax.text(50, 2, "The discipline is the same whether we predict delivery time, fraud, churn or what to recommend.",
        ha="center", fontsize=9, style="italic", color=K["clay"])
fig.savefig(CHARTS / "ml_journey.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ══ 2. Model scorecard ══
# (name, type, question, best model, key metric, vs baseline, decision, colour)
models = [
    ("Delivery-time predictor", "Regression", "How long will this order take?",
     "Ridge / Gradient Boosting", "MAE 0.96 days", "vs 1.26 naive", "Quote promises we can keep", K["ochre"]),
    ("Recommendation engine", "Market basket", "What is bought together?",
     "Association rules (lift)", f"{rb['top_lift']:.2f}x lift", "1.0 = no link", "Cross-sell proven pairs", K["teal"]),
    ("Churn model", "Classification", "Who is about to leave?",
     "Hist Gradient Boosting", "AUC 0.86", "vs 0.50 baseline", f"Win back {lc['at_risk_customers']:,} at-risk", K["plum"]),
    ("Fraud detector", "Anomaly + rules", "Which accounts are risky?",
     "Isolation Forest + rules", f"{int(rb['iso_recall']*100)}% recall", f"{int(rb['review_queue_fraud']/rb['review_queue']*100)}% queue precision", "Daily review queue", K["rust"]),
]
fig, ax = plt.subplots(figsize=(13, 6.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 96, "The Model Scorecard — four models, four decisions", ha="center",
        fontsize=14, fontweight="bold", color=K["ink"])
cols = ["Model", "Predicts", "Best algorithm", "Score", "Decision it drives"]
cx = [3, 26, 47, 68, 82]
ax.add_patch(FancyBboxPatch((2, 84), 96, 6, boxstyle="round,pad=0.1,rounding_size=0.5", fc=K["ink"], ec="none"))
for c, x in zip(cols, cx):
    ax.text(x, 87, c, fontsize=9.5, color=K["cream"], fontweight="bold", va="center")
y = 76
for name, typ, q, algo, metric, base, decision, col in models:
    ax.add_patch(FancyBboxPatch((2, y - 7), 96, 14, boxstyle="round,pad=0.1,rounding_size=0.6",
                 fc="white", ec="#eadfd3", lw=1))
    ax.add_patch(FancyBboxPatch((2, y - 7), 1.4, 14, boxstyle="round,pad=0,rounding_size=0", fc=col, ec="none"))
    ax.text(cx[0], y + 2.5, name, fontsize=9.5, fontweight="bold", color=K["ink"], va="center")
    ax.text(cx[0], y - 2.5, typ, fontsize=7.5, color=col, va="center", style="italic")
    ax.text(cx[1], y, q, fontsize=8.3, color=K["clay"], va="center")
    ax.text(cx[2], y, algo, fontsize=8.3, color=K["ink"], va="center")
    ax.text(cx[3], y + 2.5, metric, fontsize=9.5, fontweight="bold", color=col, va="center")
    ax.text(cx[3], y - 2.5, base, fontsize=7.3, color="#999", va="center")
    ax.text(cx[4], y, decision, fontsize=8.3, color=K["green"], va="center", fontweight="bold")
    y -= 15.5
ax.text(50, 3, "Note the honesty: the delivery model barely beats a linear baseline (an additive process has a "
        "natural ceiling), while fraud stacking lifts a 65%-precision model to a 91%-precision review queue.",
        ha="center", fontsize=8, style="italic", color=K["clay"], wrap=True)
fig.savefig(CHARTS / "ml_scorecard.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Rendered ml_journey.png + ml_scorecard.png")

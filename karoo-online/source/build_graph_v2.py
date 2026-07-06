"""Improved graph-database story: a proper category-affinity network built
from REAL market-basket lift, professionally styled, plus a clean PDF."""
import base64
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "out"
CHARTS = OUT / "charts"
BRAND, INK, TEAL, GOLD, SAGE = "#C0531F", "#2B2118", "#2A7F7F", "#E0A526", "#6B8E5A"

rec = pd.read_csv(OUT / "rb_recommendations.csv")

# ── Network: nodes = categories, edges weighted by lift (only lift>1.05) ──
G = nx.Graph()
cats = sorted(set(rec["antecedent"]) | set(rec["consequent"]))
for c in cats:
    G.add_node(c)
strong = rec[rec["lift"] > 1.05]
for _, r in strong.iterrows():
    G.add_edge(r["antecedent"], r["consequent"], weight=r["lift"])

# node size = total co-purchase customers involving that category
node_strength = {c: rec[(rec.antecedent == c) | (rec.consequent == c)]["pair_customers"].sum() for c in cats}

fig, ax = plt.subplots(figsize=(11, 8.5))
fig.patch.set_facecolor("white")
pos = nx.spring_layout(G, seed=11, k=1.3, weight="weight", iterations=200)

# edges: width + colour by lift
for u, v, d in G.edges(data=True):
    lift = d["weight"]
    lw = (lift - 1.0) * 22
    col = TEAL if lift >= 1.25 else GOLD if lift >= 1.12 else "#D9C3A0"
    x1, y1 = pos[u]; x2, y2 = pos[v]
    ax.plot([x1, x2], [y1, y2], color=col, lw=max(lw, 0.8), alpha=0.8, zorder=1,
            solid_capstyle="round")
    # lift label at midpoint for strong edges
    if lift >= 1.2:
        ax.text((x1+x2)/2, (y1+y2)/2, f"{lift:.2f}×", fontsize=7.5, color=INK,
                ha="center", va="center", zorder=3,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

# nodes
smax = max(node_strength.values())
for c in cats:
    x, y = pos[c]
    size = 700 + 2200 * (node_strength[c] / smax)
    ax.scatter(x, y, s=size, color=BRAND, edgecolor="white", linewidth=2.5, zorder=4, alpha=0.95)
    # label below the node in a pill so it never clips the circle
    ax.text(x, y - 0.115, c, fontsize=9, color=INK, ha="center", va="center", zorder=6,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#E8D5C0", lw=1, alpha=0.95))

ax.set_title("Category Affinity Network — what's genuinely bought together\n"
             "(edge thickness & label = lift; node size = co-purchase volume)",
             fontsize=14, fontweight="bold", color=INK, pad=16)
ax.axis("off")
# legend
from matplotlib.lines import Line2D
leg = [Line2D([0], [0], color=TEAL, lw=4, label="Strong (lift ≥ 1.25)"),
       Line2D([0], [0], color=GOLD, lw=3, label="Moderate (1.12–1.25)"),
       Line2D([0], [0], color="#D9C3A0", lw=2, label="Weak (1.05–1.12)")]
ax.legend(handles=leg, loc="lower right", fontsize=9, framealpha=0.9)
fig.savefig(CHARTS / "affinity_network.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("Rendered affinity_network.png")


def img(name):
    return f'<img src="data:image/png;base64,{base64.b64encode((CHARTS/name).read_bytes()).decode()}" style="max-width:100%;border-radius:8px;">'


top = strong.sort_values("lift", ascending=False).head(8)
rows = "".join(f"<tr><td><b>{r.antecedent}</b> + <b>{r.consequent}</b></td>"
               f"<td class='num'>{r.lift:.2f}×</td><td class='num'>{r.confidence*100:.0f}%</td>"
               f"<td class='num'>{int(r.pair_customers):,}</td></tr>" for _, r in top.iterrows())

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page{{size:A4;margin:16mm;}}
body{{font-family:'Segoe UI',Arial,sans-serif;color:#2B2118;line-height:1.55;}}
h1{{color:#C0531F;}}h2{{color:#C0531F;border-bottom:2px solid #C0531F;padding-bottom:4px;margin-top:22px;}}
.cover{{text-align:center;padding-top:150px;page-break-after:always;}}
.lesson{{background:#FDF6E3;border-left:4px solid #E0A526;border-radius:0 8px 8px 0;padding:12px 16px;margin:14px 0;}}
.lesson b{{color:#a5720f;}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:10px 0;}}
th{{background:#2B2118;color:#FBF3EC;padding:7px 9px;text-align:left;}}
td{{padding:6px 9px;border-bottom:1px solid #eee;}}td.num{{text-align:right;}}
tr:nth-child(even) td{{background:#fbf7f2;}}
pre{{background:#2B2118;color:#F5E9DC;padding:12px;border-radius:6px;font-size:11px;}}
</style></head><body>

<div class="cover"><h1>KAROO ONLINE — THE AFFINITY GRAPH</h1>
<p style="color:#7A4A2B;font-size:16px">Graph analytics: the relationships SQL can't see<br>
Turning a million orders into a recommendation network</p>
<p style="margin-top:50px">Anthony Apollis · 2026</p></div>

<h2>Why a graph view?</h2>
<p>Rows and totals answer "how much". A <b>graph</b> answers "what connects to what". By modelling
customers and the categories they buy as a network, the products that genuinely travel together
emerge as the strongest edges — the raw material of a recommendation engine.</p>

<h2>The Category Affinity Network</h2>
{img('affinity_network.png')}
<div class="lesson"><b>How to read it:</b> each node is a category (bigger = more co-purchase
volume); each edge is a genuine "bought-together" relationship, thicker and greener the stronger
the lift. Unlike a raw correlation, <b>lift controls for how popular each category already is</b> —
so a strong edge means a real affinity, not just two common categories coinciding.</div>

<h2>The strongest affinities</h2>
<table><tr><th>Bought together</th><th>Lift</th><th>Confidence</th><th>Customers</th></tr>{rows}</table>
<div class="lesson"><b>So what — the business use:</b> these pairs drive three concrete actions:
<b>(1)</b> "customers also bought" widgets on product pages, <b>(2)</b> cart cross-sell prompts,
and <b>(3)</b> bundle promotions. Because the edges are ranked by lift, the team knows exactly which
pairings to surface first — the highest-ROI output of the entire analytics pipeline.</div>

<h2>Why a graph database (Neptune) in production</h2>
<p>At small scale this network is computed with a SQL market-basket query. At marketplace scale —
millions of customers, deep multi-hop questions like "customers similar to those who bought X, via
shared brand <i>and</i> province" — a dedicated graph database (Amazon Neptune) answers in a single
traversal what SQL would need many escalating self-joins to express. The rule holds: <b>counts and
totals → SQL; paths and relationships → graph</b>.</p>

</body></html>"""

(OUT / "Karoo_Online_Affinity_Graph.html").write_text(html, encoding="utf-8")
pdf = OUT / "Karoo_Online_Affinity_Graph.pdf"
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([edge, "--headless", "--disable-gpu", f"--print-to-pdf={pdf}",
                "--no-pdf-header-footer", str(OUT / "Karoo_Online_Affinity_Graph.html")], check=True, timeout=120)
print("PDF:", pdf)

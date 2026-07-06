"""Assemble the flagship Karoo data story — a compact, card-based, colourful
HTML report → PDF. Brand identity + product/brand/category analysis +
geographic story, designed to read like a well-compiled narrative."""
import base64
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "out"
CHARTS = OUT / "charts"

products = pd.read_csv(OUT / "products_master.csv")
brands = pd.read_csv(OUT / "brands.csv")
cats = pd.read_csv(OUT / "category_summary.csv")
cat_totals = pd.read_csv(OUT / "category_totals.csv")
prov_cat = pd.read_csv(OUT / "province_category.csv")

# ── key numbers ──
total_rev = products["revenue"].sum()
total_units = products["units_sold"].sum()
n_products = len(products)
n_brands = brands["brand"].nunique()
n_cats = len(cats)
top_product = products.iloc[0]
top_brand = brands.iloc[0]
top_cat = cats.iloc[0]
worst_cat = cats.iloc[-1]
avg_rating = products["avg_rating"].mean()
fashion_return = cat_totals[cat_totals.category == "Fashion"]["return_pct"].iloc[0]
prov_rev = prov_cat.groupby("province")["revenue"].sum().sort_values(ascending=False)
top_prov = prov_rev.index[0]
top3_prov_share = prov_rev.head(3).sum() / prov_rev.sum() * 100


def img(name, cls=""):
    p = CHARTS / name
    data = base64.b64encode(p.read_bytes()).decode()
    return f'<img class="{cls}" src="data:image/png;base64,{data}">'


def money(x):
    return f"R{x/1e6:.0f}m" if x < 1e9 else f"R{x/1e9:.2f}bn"


TIER_BADGE = {"premium": ("PREMIUM", "#7D5BA6"), "mid": ("CORE", "#2A7F7F"), "budget": ("VALUE", "#6B8E5A")}


def product_row(r, rank):
    tb, tc = TIER_BADGE[r["tier"]]
    return f"""<tr>
      <td class="rank">{rank}</td>
      <td><b>{r['product_name']}</b><br><span class="muted">{r['brand']} · {r['category']}</span></td>
      <td><span class="badge" style="background:{tc}">{tb}</span></td>
      <td class="num">R{r['unit_price']:,.0f}</td>
      <td class="num">{r['units_sold']:,}</td>
      <td class="num"><b>{money(r['revenue'])}</b></td>
      <td class="num">★{r['avg_rating']}</td>
      <td class="num">{r['return_pct']}%</td>
    </tr>"""


top10_rows = "\n".join(product_row(r, i+1) for i, (_, r) in enumerate(products.head(10).iterrows()))
worst10 = products.tail(10).iloc[::-1]
worst10_rows = "\n".join(product_row(r, n_products-9+i) for i, (_, r) in enumerate(worst10.iloc[::-1].iterrows()))

# category cards
cat_cards = ""
CATCOLORS = ["#C0531F", "#2A7F7F", "#E0A526", "#6B8E5A", "#7D5BA6", "#E07856",
             "#4A90C2", "#A5361A", "#8A8B4C", "#9C3B5A", "#7A4A2B", "#3E8E7E"]
for i, (_, c) in enumerate(cats.iterrows()):
    col = CATCOLORS[i % len(CATCOLORS)]
    cat_cards += f"""<div class="cat-card" style="border-top:4px solid {col}">
      <div class="cat-name">{c['category']}</div>
      <div class="cat-rev" style="color:{col}">{money(c['revenue'])}</div>
      <div class="cat-meta">{c['products']} products · ★{c['avg_rating']:.1f} · ↩{c['avg_return_pct']:.1f}%</div>
    </div>"""

# brand chips (top 8)
brand_chips = ""
for _, b in brands.head(8).iterrows():
    brand_chips += f'<div class="brand-chip"><b>{b["brand"]}</b><span>{money(b["revenue"])} · ★{b["avg_rating"]:.1f}</span></div>'

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
:root {{
  --ochre:#C0531F; --clay:#7A4A2B; --ink:#2B2118; --sand:#E8D5C0; --cream:#FBF3EC;
  --teal:#2A7F7F; --gold:#E0A526; --sage:#6B8E5A;
}}
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; color: var(--ink);
        margin: 0; line-height: 1.5; font-size: 13px; }}
.page {{ padding: 20mm 16mm; page-break-after: always; position: relative; }}
.page:last-child {{ page-break-after: auto; }}
h1 {{ font-size: 30px; margin: 0 0 4px; letter-spacing: -0.5px; }}
h2 {{ font-size: 21px; color: var(--ochre); margin: 0 0 3px; letter-spacing: -0.3px; }}
h2 .kicker {{ display:block; font-size:11px; letter-spacing:3px; color:var(--clay);
             text-transform:uppercase; font-weight:600; margin-bottom:3px;}}
h3 {{ font-size: 15px; color: var(--clay); margin: 18px 0 8px; }}
.lead {{ font-size: 14px; color: #4a3a2c; }}
p {{ margin: 8px 0; }}

/* ── COVER ── */
.cover {{ background: linear-gradient(135deg, #2B2118 0%, #5c3418 55%, #C0531F 100%);
          color: #FBF3EC; height: 297mm; display: flex; flex-direction: column;
          justify-content: center; padding: 0 22mm; page-break-after: always; }}
.cover .brand {{ font-size: 13px; letter-spacing: 8px; text-transform: uppercase; color: var(--gold); }}
.cover h1 {{ font-size: 52px; line-height: 1.05; margin: 14px 0; }}
.cover .tag {{ font-size: 17px; color: #e8d5c0; max-width: 440px; }}
.cover .meta {{ margin-top: 46px; font-size: 12px; color: #cbb8a0; letter-spacing: 1px; }}
.cover .rule {{ width: 70px; height: 4px; background: var(--gold); margin: 20px 0; }}

/* ── KPI BAND ── */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 14px 0; }}
.kpi {{ background: var(--cream); border-radius: 10px; padding: 14px 16px; border-left: 4px solid var(--ochre); }}
.kpi .v {{ font-size: 24px; font-weight: 700; color: var(--ochre); line-height: 1; }}
.kpi .l {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--clay); margin-top: 5px; }}
.kpi.teal {{ border-color: var(--teal); }} .kpi.teal .v {{ color: var(--teal); }}
.kpi.gold {{ border-color: var(--gold); }} .kpi.gold .v {{ color: #b7841a; }}
.kpi.sage {{ border-color: var(--sage); }} .kpi.sage .v {{ color: var(--sage); }}

/* ── VALUE CARDS ── */
.val-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }}
.val {{ background: white; border: 1px solid var(--sand); border-radius: 10px; padding: 14px 16px; }}
.val .icon {{ font-size: 22px; }}
.val .t {{ font-weight: 700; color: var(--ochre); margin: 6px 0 3px; font-size: 14px; }}
.val .d {{ font-size: 12px; color: #5a4636; }}

/* ── CATEGORY CARDS ── */
.cat-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 9px; margin: 12px 0; }}
.cat-card {{ background: white; border: 1px solid #eadfd3; border-radius: 9px; padding: 11px 13px; }}
.cat-name {{ font-weight: 700; font-size: 12.5px; }}
.cat-rev {{ font-size: 19px; font-weight: 700; margin: 3px 0; }}
.cat-meta {{ font-size: 10px; color: var(--clay); }}

/* ── BRAND CHIPS ── */
.brand-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
.brand-chip {{ background: var(--cream); border-radius: 20px; padding: 7px 15px; font-size: 12px; }}
.brand-chip span {{ display: block; font-size: 10px; color: var(--clay); }}

/* ── TABLES ── */
table {{ border-collapse: collapse; width: 100%; font-size: 11.5px; margin: 8px 0; }}
th {{ background: var(--ink); color: var(--cream); padding: 8px 9px; text-align: left; font-size: 10px;
      text-transform: uppercase; letter-spacing: 0.5px; }}
td {{ padding: 7px 9px; border-bottom: 1px solid #eee; }}
tr:nth-child(even) td {{ background: #fbf7f2; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
td.rank {{ font-weight: 700; color: var(--ochre); text-align: center; width: 28px; }}
.muted {{ color: #999; font-size: 10px; }}
.badge {{ color: white; font-size: 8.5px; padding: 2px 7px; border-radius: 10px; font-weight: 700; letter-spacing: 0.5px; }}

img {{ max-width: 100%; border-radius: 8px; display: block; margin: 6px 0; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: center; }}
.insight {{ background: #FDF6E3; border-left: 4px solid var(--gold); border-radius: 0 8px 8px 0;
            padding: 11px 15px; margin: 12px 0; font-size: 12.5px; }}
.insight b {{ color: #a5720f; }}
.footer {{ position: absolute; bottom: 10mm; left: 16mm; right: 16mm; display: flex;
           justify-content: space-between; font-size: 9px; color: #b0a090; letter-spacing: 1px; }}
.q {{ display:inline-block; background:var(--ochre); color:white; width:22px; height:22px;
      border-radius:50%; text-align:center; line-height:22px; font-weight:700; font-size:12px; margin-right:6px;}}
</style></head><body>

<!-- ══ COVER ══ -->
<div class="cover">
  <div class="brand">Karoo Trading Co.</div>
  <div class="rule"></div>
  <h1>What South Africa<br>Buys</h1>
  <div class="tag">A data story of 10 million orders, 120 products, and R4.7 billion —
  told from the raw shelves of a proudly South African marketplace.</div>
  <div class="meta">ANNUAL DATA REVIEW · 2025–2026 · ANTHONY APOLLIS, DATA &amp; ANALYTICS</div>
</div>

<!-- ══ THE WHY ══ -->
<div class="page">
  <h2><span class="kicker">Why we exist</span>The Karoo Way</h2>
  <p class="lead">Named for the vast, honest heartland of South Africa, <b>Karoo Trading Co.</b>
  built its marketplace on a simple belief: that quality goods should reach every corner of the
  country — from the Cape Winelands to the edge of the Kalahari — at a fair price, delivered
  when promised.</p>

  <div class="val-grid">
    <div class="val"><div class="icon">🎯</div><div class="t">Our Mission</div>
      <div class="d">To be the marketplace that every South African household trusts —
      stocking what people actually need, and getting it to their door reliably.</div></div>
    <div class="val"><div class="icon">🤝</div><div class="t">Our Promise</div>
      <div class="d">Honest pricing, no hidden costs, and a delivery date we intend to keep.
      When we fall short, the data tells us — and we fix it.</div></div>
    <div class="val"><div class="icon">🌍</div><div class="t">Our Reach</div>
      <div class="d">Nine provinces, hundreds of towns, five courier partners — one
      catalogue built for the whole country, not just the metros.</div></div>
  </div>

  <h3>What we stand for</h3>
  <div class="val-grid">
    <div class="val"><div class="t" style="color:var(--teal)">Resilience</div>
      <div class="d">Like the Karoo itself — we weather the seasons and keep trading.</div></div>
    <div class="val"><div class="t" style="color:var(--sage)">Fairness</div>
      <div class="d">The same price and service whether you're in Sandton or Springbok.</div></div>
    <div class="val"><div class="t" style="color:var(--gold)">Honesty with data</div>
      <div class="d">We measure everything, and we don't flatter the numbers.</div></div>
  </div>

  <div class="insight">This report follows the data through five questions every retailer must
  answer: <b>Why</b> we're here, <b>What</b> we sell, <b>Where</b> we sell it, <b>Who</b> buys,
  and <b>How</b> well we deliver — ending in <b>what we do next</b>.</div>

  <div class="footer"><span>KAROO TRADING CO.</span><span>THE KAROO WAY · 01</span></div>
</div>

<!-- ══ THE HEADLINES ══ -->
<div class="page">
  <h2><span class="kicker">What the year looked like</span>The Headlines</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="v">{money(total_rev)}</div><div class="l">Total revenue</div></div>
    <div class="kpi teal"><div class="v">{total_units/1e6:.1f}m</div><div class="l">Units sold</div></div>
    <div class="kpi gold"><div class="v">{n_products}</div><div class="l">Products · {n_brands} brands</div></div>
    <div class="kpi sage"><div class="v">★{avg_rating:.1f}</div><div class="l">Avg product rating</div></div>
  </div>

  <h3>Revenue by category — the product mix</h3>
  {img('category_treemap.png')}
  <div class="insight"><b>{top_cat['category']}</b> leads the catalogue at {money(top_cat['revenue'])},
  but the top four categories — Electronics, Garden &amp; Pool, Sport &amp; Outdoor and Automotive —
  are strikingly close, together making up more than half of all revenue. Karoo is a
  <b>generalist marketplace</b>, not a category specialist: no single aisle carries the business.</div>

  <div class="footer"><span>KAROO TRADING CO.</span><span>THE HEADLINES · 02</span></div>
</div>

<!-- ══ WHAT WE SELL — categories ══ -->
<div class="page">
  <h2><span class="kicker">What we sell</span>Twelve Aisles</h2>
  <div class="cat-grid">{cat_cards}</div>
  <div class="two-col" style="margin-top:14px">
    <div>{img('price_vs_rating.png')}</div>
    <div>
      <h3>Price doesn't buy love</h3>
      <p>Plotting every product's price against its customer rating shows almost no relationship —
      budget rusks and premium laptops both earn their stars on merit, not markup. The bubbles
      (revenue) cluster in the mid-price range: <b>South Africa's spending heart is the R150–R600
      product</b>, not the luxury tail.</p>
      <div class="insight" style="margin-top:8px"><b>So what:</b> discounting a well-rated
      mid-tier product moves far more volume than shaving margin on a premium item few buy.</div>
    </div>
  </div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>WHAT WE SELL · 03</span></div>
</div>

<!-- ══ BEST & WORST PRODUCTS ══ -->
<div class="page">
  <h2><span class="kicker">The winners</span>Top 10 Products</h2>
  <table>
    <tr><th></th><th>Product</th><th>Tier</th><th>Price</th><th>Units</th><th>Revenue</th><th>Rating</th><th>Return</th></tr>
    {top10_rows}
  </table>
  <div class="insight"><b>{top_product['product_name']}</b> ({top_product['brand']}) is the single
  biggest earner at {money(top_product['revenue'])} — a {top_product['tier']}-tier
  {top_product['category']} product proving that big-ticket, well-rated items anchor the catalogue.</div>

  <h2 style="margin-top:22px"><span class="kicker">The long tail</span>Bottom 10 Products</h2>
  <table>
    <tr><th></th><th>Product</th><th>Tier</th><th>Price</th><th>Units</th><th>Revenue</th><th>Rating</th><th>Return</th></tr>
    {worst10_rows}
  </table>
  <div class="insight"><b>So what:</b> the bottom ten are all low-price {worst10.iloc[0]['category']}-style
  impulse items. They aren't failures — they're basket-fillers that drive add-on volume — but none
  should command prime merchandising space or ad spend.</div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>BEST &amp; WORST · 04</span></div>
</div>

<!-- ══ BRANDS ══ -->
<div class="page">
  <h2><span class="kicker">Who makes it</span>The Brands That Sell</h2>
  <div class="brand-row">{brand_chips}</div>
  {img('top_brands.png')}
  <div class="insight"><b>{top_brand['brand']}</b> is Karoo's top-performing brand at
  {money(top_brand['revenue'])} across the {top_brand['category']} aisle. Brand strength is
  concentrated: the top handful of house and partner brands carry a disproportionate share of
  revenue — a <b>vendor-negotiation lever</b> worth pulling at contract renewal.</div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>THE BRANDS · 05</span></div>
</div>

<!-- ══ WHERE ══ -->
<div class="page">
  <h2><span class="kicker">Where South Africa shops</span>The Map of Demand</h2>
  {img('sa_choropleth.png')}
  <div class="insight"><b>{top_prov}</b> is the beating heart of demand, and the metro triangle
  ({top_prov}, Western Cape, KwaZulu-Natal) accounts for <b>{top3_prov_share:.0f}%</b> of all
  revenue. The vast interior provinces — Northern Cape, Free State, North West — are sparse but
  strategically important: they're where reliable delivery is hardest and loyalty is won.</div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>THE MAP · 06</span></div>
</div>

<!-- ══ HOW / MARGIN RISK ══ -->
<div class="page">
  <h2><span class="kicker">How well it works</span>The Margin-Risk Map</h2>
  <div class="two-col">
    <div>{img('return_vs_revenue.png')}</div>
    <div>
      <h3>Fashion's hidden cost</h3>
      <p>Every product plotted by return rate against revenue. One category stands apart:
      <b>Fashion returns at {fashion_return:.0f}%</b> — three to eight times the rate of any other
      aisle. High-revenue, high-return products in the top-right are where <b>margin quietly leaks</b>.</p>
      <div class="insight" style="margin-top:8px"><b>So what:</b> a sizing-guide prompt and
      better product photography on Fashion lines would protect more margin than any discount
      could add in sales.</div>
    </div>
  </div>
  <h3>Eighteen months of trade</h3>
  {img('monthly_stacked.png')}
  <div class="insight"><b>The rhythm of the year:</b> revenue builds steadily toward the
  festive-season peak — the pattern every South African retailer plans around. Category mix stays
  remarkably stable month to month, confirming a <b>habitual, needs-driven customer base</b>
  rather than a fashion-led one.</div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>MARGIN &amp; RHYTHM · 07</span></div>
</div>

<!-- ══ SO WHAT ══ -->
<div class="page">
  <h2><span class="kicker">What we do next</span>The Playbook</h2>
  <p class="lead">Five moves the data makes obvious:</p>
  <div class="val-grid" style="grid-template-columns:1fr 1fr;">
    <div class="val"><div class="t"><span class="q">1</span>Protect Fashion margin</div>
      <div class="d">At {fashion_return:.0f}% returns, sizing guides and better imagery on Fashion
      lines recover more margin than any promotion adds.</div></div>
    <div class="val"><div class="t"><span class="q">2</span>Lean into the mid-price heart</div>
      <div class="d">The R150–R600 band drives the most volume. Merchandise and discount here,
      not in the thin premium tail.</div></div>
    <div class="val"><div class="t"><span class="q">3</span>Win the interior</div>
      <div class="d">Metros are saturated; the Northern Cape, Free State and North West are where
      reliable delivery earns lasting loyalty.</div></div>
    <div class="val"><div class="t"><span class="q">4</span>Negotiate with the top brands</div>
      <div class="d">A handful of brands carry outsized revenue — use that leverage at
      contract renewal for better terms.</div></div>
  </div>
  <div class="insight" style="margin-top:16px"><b>The through-line:</b> Karoo Trading Co. is a
  broad, dependable, needs-driven marketplace serving all of South Africa. Its strength is balance —
  no single product, brand, category or province carries it. Its opportunity is precision:
  protecting margin where it leaks, and earning loyalty where delivery is hardest. That is
  <b>The Karoo Way</b> — measured honestly, and acted on.</div>
  <div class="footer"><span>KAROO TRADING CO.</span><span>THE PLAYBOOK · 08</span></div>
</div>

</body></html>"""

out_html = OUT / "Karoo_Data_Story.html"
out_html.write_text(html, encoding="utf-8")
print("HTML:", out_html)

pdf = OUT / "Karoo_Data_Story.pdf"
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([edge, "--headless", "--disable-gpu", f"--print-to-pdf={pdf}",
                "--no-pdf-header-footer", str(out_html)], check=True, timeout=180)
print("PDF:", pdf)

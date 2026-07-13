"""Karoo Online flagship — interactive HTML (Netlify) + static PDF.
Marketplace catalogue + behavioural analyses + full marketing spectrum +
data provenance. Terse, scannable copy (charts carry the story)."""
import base64
import json
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "out"
CHARTS = OUT / "charts"

tk = json.load(open(OUT / "tk_summary.json"))
rb = json.load(open(OUT / "rb_summary.json"))
mk = json.load(open(OUT / "mkt_summary.json"))
lc = json.load(open(OUT / "lifecycle_summary.json"))
oil = json.load(open(OUT / "oil_summary.json"))
tk_cat = pd.read_csv(OUT / "tk_category_summary.csv")
tk_clean = pd.read_csv(OUT / "takealot_products_clean.csv")
rec = pd.read_csv(OUT / "rb_recommendations.csv")
pstats = pd.read_csv(OUT / "province_stats.csv")
paid = pd.read_csv(OUT / "mkt_paid_by_channel.csv")
top3 = pstats.head(3)["revenue_share_pct"].sum()
map_fragment = (OUT / "interactive_map_fragment.html").read_text(encoding="utf-8")
ts_fragment = (OUT / "interactive_timeseries_fragment.html").read_text(encoding="utf-8")
ts = json.load(open(OUT / "timeseries_summary.json"))


def img(name):
    return f'<img src="data:image/png;base64,{base64.b64encode((CHARTS/name).read_bytes()).decode()}">'


# top real products (most expensive) — compact
tk_pr = tk_clean[tk_clean["price"] > 0].sort_values("price", ascending=False)
top_rows = ""
for _, r in tk_pr.head(6).iterrows():
    brand = r["brand"] if isinstance(r["brand"], str) and r["brand"].strip() else "<span class='muted'>unbranded</span>"
    top_rows += f"<tr><td><b>{r['title'][:52]}</b></td><td>{brand}</td><td class='num'>R{r['price']:,.0f}</td></tr>"

cat_cards = ""
CC = ["#C0531F", "#2A7F7F", "#E0A526", "#6B8E5A", "#7D5BA6", "#E07856", "#4A90C2", "#A5361A"]
for i, (_, c) in enumerate(tk_cat.head(8).iterrows()):
    col = CC[i % len(CC)]
    cat_cards += (f'<div class="cat-card" style="border-top:4px solid {col}">'
                  f'<div class="cat-name">{c["category"]}</div>'
                  f'<div class="cat-rev" style="color:{col}">{int(c["products"])}</div>'
                  f'<div class="cat-meta">median R{c["median_price"]:.0f}</div></div>')

rec_rows = ""
for _, r in rec.head(5).iterrows():
    rec_rows += (f"<tr><td><b>{r['antecedent']}</b> + <b>{r['consequent']}</b></td>"
                 f"<td class='num'>{r['lift']:.2f}×</td><td class='num'>{r['confidence']*100:.0f}%</td></tr>")

paid_rows = ""
for _, r in paid.iterrows():
    paid_rows += (f"<tr><td><b>{r['channel']}</b></td><td class='num'>R{r['spend']/1e6:.1f}m</td>"
                  f"<td class='num'>R{r['revenue']/1e6:.1f}m</td><td class='num'><b>{r['roas']:.1f}×</b></td></tr>")

CSS = """
:root{--ochre:#C0531F;--clay:#7A4A2B;--ink:#2B2118;--sand:#E8D5C0;--cream:#FBF3EC;--teal:#2A7F7F;--gold:#E0A526;--sage:#6B8E5A;--rust:#A5361A;}
*{box-sizing:border-box;}
body{font-family:'Segoe UI',Helvetica,Arial,sans-serif;color:var(--ink);margin:0;line-height:1.45;font-size:13px;}
.page{padding:18mm 16mm;position:relative;}
h2{font-size:22px;color:var(--ochre);margin:0 0 10px;letter-spacing:-0.3px;}
h2 .kicker{display:block;font-size:11px;letter-spacing:3px;color:var(--clay);text-transform:uppercase;font-weight:600;margin-bottom:3px;}
h3{font-size:14px;color:var(--clay);margin:14px 0 6px;}
.cover{background:linear-gradient(135deg,#2B2118 0%,#5c3418 55%,#C0531F 100%);color:#FBF3EC;min-height:297mm;display:flex;flex-direction:column;justify-content:center;padding:0 22mm;}
.cover .brand{font-size:13px;letter-spacing:8px;text-transform:uppercase;color:var(--gold);}
.cover h1{font-size:52px;line-height:1.05;margin:14px 0;}
.cover .tag{font-size:16px;color:#e8d5c0;max-width:440px;}
.cover .meta{margin-top:44px;font-size:12px;color:#cbb8a0;letter-spacing:1px;}
.cover .rule{width:70px;height:4px;background:var(--gold);margin:20px 0;}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;}
.kpi{background:var(--cream);border-radius:10px;padding:13px 15px;border-left:4px solid var(--ochre);}
.kpi .v{font-size:23px;font-weight:700;color:var(--ochre);line-height:1;}
.kpi .l{font-size:9.5px;text-transform:uppercase;letter-spacing:0.5px;color:var(--clay);margin-top:5px;}
.kpi.teal{border-color:var(--teal);}.kpi.teal .v{color:var(--teal);}
.kpi.gold{border-color:var(--gold);}.kpi.gold .v{color:#b7841a;}
.kpi.sage{border-color:var(--sage);}.kpi.sage .v{color:var(--sage);}
.val-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:11px;margin:10px 0;}
.val{background:white;border:1px solid var(--sand);border-radius:10px;padding:13px 15px;}
.val .t{font-weight:700;color:var(--ochre);margin:0 0 3px;font-size:13.5px;}
.val .d{font-size:12px;color:#5a4636;}
.cat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:10px 0;}
.cat-card{background:white;border:1px solid #eadfd3;border-radius:9px;padding:10px 12px;}
.cat-name{font-weight:700;font-size:12px;}.cat-rev{font-size:22px;font-weight:700;margin:1px 0;}
.cat-meta{font-size:10px;color:var(--clay);}
table{border-collapse:collapse;width:100%;font-size:11.5px;margin:6px 0;}
th{background:var(--ink);color:var(--cream);padding:7px 9px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:0.5px;}
td{padding:6px 9px;border-bottom:1px solid #eee;}tr:nth-child(even) td{background:#fbf7f2;}
td.num{text-align:right;font-variant-numeric:tabular-nums;}.muted{color:#999;}
img{max-width:100%;border-radius:8px;display:block;margin:5px 0;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:center;}
.take{background:#FDF6E3;border-left:4px solid var(--gold);border-radius:0 8px 8px 0;padding:9px 14px;margin:10px 0;font-size:12.5px;}
.take b{color:#a5720f;}
.footer{margin-top:16px;padding-top:8px;border-top:1px solid #eadfd3;display:flex;justify-content:space-between;font-size:9px;color:#b0a090;letter-spacing:1px;}
.mapwrap{border:1px solid #eadfd3;border-radius:10px;overflow:hidden;margin:8px 0;background:white;}
.q{display:inline-block;background:var(--ochre);color:white;width:20px;height:20px;border-radius:50%;text-align:center;line-height:20px;font-weight:700;font-size:11px;margin-right:5px;}
"""


def body(map_html, ts_html, web=False):
    pb = "page-break-after:always;" if not web else "margin-bottom:22px;border-bottom:2px solid #f0e6da;"
    return f"""
<div class="cover" style="{pb}">
  <div class="brand">Karoo Online</div><div class="rule"></div>
  <h1>What South Africa<br>Buys Online</h1>
  <div class="tag">A real 1,000-product catalogue, a million orders, and the marketing and machine
  learning that turn them into decisions.</div>
  <div class="meta">DATA &amp; ANALYTICS REVIEW · 4 YEARS: JUL 2022 – JUN 2026 · ANTHONY APOLLIS</div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Why we exist</span>The Karoo Way</h2>
  <div class="val-grid">
    <div class="val"><div class="t">Mission</div><div class="d">The online marketplace every South
    African household trusts — stocking what people need, delivered reliably.</div></div>
    <div class="val"><div class="t">Promise</div><div class="d">Honest pricing and a delivery date we
    keep. When we fall short, the data tells us.</div></div>
    <div class="val"><div class="t">Reach</div><div class="d">Nine provinces, one catalogue built for
    the whole country — not just the metros.</div></div>
  </div>
  <div class="take">Five questions, answered with data: <b>what</b> we sell · <b>where</b> demand lives ·
  <b>what</b> customers buy together · <b>which</b> marketing pays · <b>who</b> to watch for fraud.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>01</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Where the data comes from</span>One Central Source of Truth</h2>
  {img('data_provenance.png')}
  <div class="take">Five sources — a marketplace catalogue, web &amp; app analytics, orders and marketing —
  land in <b>one governed lakehouse</b> (<code>karoo_db</code> on AWS). Every insight reads from that
  single source, so <b>the figures always agree</b>. <b>Time horizons:</b> the revenue history spans
  <b>four years (Jul 2022 – Jun 2026)</b> for trend and seasonality, while the deep-dive analyses
  (catalogue, behaviour, churn, fraud) focus on the most recent <b>trailing period</b> for freshness.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>DATA PROVENANCE · 02</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">How the web data is captured</span>Google Tag Manager in Action</h2>
  <p style="font-size:12.5px;margin:2px 0 8px">Before any analysis, the behaviour has to be <i>captured</i>.
  Google Tag Manager sits on the storefront and fires a tracked <code>dataLayer</code> event at every step of
  the journey — which flows to GA4 and into the lakehouse. This is the front door of the whole pipeline.</p>
  <div class="two-col"><div>{img('gtm_shot1.png')}</div><div>{img('gtm_shot2.png')}</div></div>
  <div class="take"><b>Why it matters:</b> clean, structured event capture at the source is what makes the funnel,
  attribution and recommendation analysis later in this report possible. <b>No tags, no data — no insight.</b>
  Each purchase event carries its value and transaction ID, so revenue ties out from click to checkout.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>DATA CAPTURE (GTM) · 03</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Why you can trust the numbers</span>How the Figures Reconcile</h2>
  <p style="font-size:12.5px;margin:2px 0 8px">A report is only as good as its numbers. Here is how every
  figure in this document is <b>reconciled</b> — guaranteed to agree from the moment of the sale to the KPI
  on the page — and the technology that makes that possible.</p>
  {img('reconciliation.png')}
  <div class="take"><b>The principle — one source of truth:</b> the value captured at checkout is the <i>same</i>
  value that lands in S3, gets transformed by Athena, and appears in this report. Nothing is re-keyed or
  re-estimated along the way. <b>Validation gates</b> (null, duplicate, referential-integrity and
  revenue cross-checks) run <i>before</i> any figure is trusted — our catalogue-to-orders join, for example,
  resolved <b>100% of IDs</b>. <b>The tech guarantees it:</b> a single Glue catalogue means every tool reads
  one schema; an immutable S3 raw zone means the source never shifts; deterministic Athena ETL means the same
  input always yields the same output; and Terraform means the whole pipeline is reproducible on demand. That
  is why, across catalogue, marketing, customers and finance, <b>the figures always agree</b>.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>RECONCILIATION · 04</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">What we sell · real catalogue</span>1,000 Real Products</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="v">R{tk['price_median']:,}</div><div class="l">Median price · R{tk['price_min']}–R{tk['price_max']:,}</div></div>
    <div class="kpi teal"><div class="v">{tk['n_categories']}</div><div class="l">Categories</div></div>
    <div class="kpi gold"><div class="v">{tk['pct_in_stock']}%</div><div class="l">In stock (fast)</div></div>
    <div class="kpi sage"><div class="v">{tk['pct_lead_time']}%</div><div class="l">Import lead time</div></div>
  </div>
  <div class="cat-grid">{cat_cards}</div>
  <div class="two-col">
    <div>{img('tk_price_dist.png')}</div>
    <div>{img('tk_availability.png')}</div>
  </div>
  <div class="take"><b>Availability beats price:</b> only {tk['pct_in_stock']}% ships fast; {tk['pct_lead_time']}%
  is imported on 4–16 day lead times. Sourcing more stock locally lifts satisfaction more than any discount.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>THE CATALOGUE · 03</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Where demand lives</span>The Interactive Map</h2>
  <div class="mapwrap">{map_html}</div>
  <div class="take"><b>Metro vs interior:</b> the top 3 provinces are {top3:.0f}% of revenue and deliver
  <b>72% on-time in 2.9 days</b> — the interior manages just <b>32% in 4.7 days</b>. Geography, not
  courier, decides speed. {"<b>Hover any province for its full stats.</b>" if web else "<i>(Interactive in the web edition.)</i>"}</div>
  <div class="footer"><span>KAROO ONLINE</span><span>THE MAP · 04</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Four years of growth · pick your window</span>Revenue Over Time</h2>
  <p style="font-size:12.5px;margin:2px 0 8px">The full trading history — <b>{ts['start']} to {ts['end']}</b>,
  {ts['months']} months. {"<b>Use the 1Y / 2Y / 4Y buttons or drag the slider</b> to choose a time frame; the oil-crisis window is shaded." if web else "Festive peaks each November, ~"+str(ts['cagr_pct'])+"% annual growth, and the 2026 oil-crisis dip are all visible."}</p>
  {('<div class="mapwrap">'+ts_html+'</div>') if web else img('ts_4yr.png')}
  <div class="take"><b>The trajectory:</b> ~<b>{ts['cagr_pct']}% annual growth</b> over four years to
  R{ts['latest_month_rev_m']}m in the latest month, with a clear festive spike every November and a visible
  dip during the 2026 oil crisis. Total revenue across the period: <b>R{ts['total_revenue_bn']}bn</b>.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>REVENUE OVER TIME · 05</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Which marketing pays</span>Paid &amp; Remarketing</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="v">{mk['paid_roas']:.1f}×</div><div class="l">Blended paid ROAS</div></div>
    <div class="kpi teal"><div class="v">{mk['remarketing_roas']:.1f}×</div><div class="l">Remarketing ROAS</div></div>
    <div class="kpi gold"><div class="v">R{mk['total_marketing_revenue']/1e6:.0f}m</div><div class="l">Marketing revenue</div></div>
    <div class="kpi sage"><div class="v">{mk['best_paid_channel']}</div><div class="l">Best channel ({mk['best_paid_roas']:.1f}×)</div></div>
  </div>
  <div class="two-col">
    <div>{img('mkt_paid.png')}</div>
    <div>{img('mkt_remarketing.png')}</div>
  </div>
  <div class="take"><b>Remarketing is the cheat code:</b> {mk['best_remarketing']} returns
  {mk['best_remarketing_roas']:.0f}× — put budget into recovering carts before chasing new clicks.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>PAID MARKETING · 05</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Free traffic &amp; the AI frontier</span>SEO &amp; AI Visibility</h2>
  <div class="two-col">
    <div>{img('mkt_seo.png')}</div>
    <div>{img('mkt_keywords.png')}</div>
  </div>
  <h3>AI visibility — being found inside AI answers</h3>
  <div class="two-col">
    <div>{img('mkt_ai_sov.png')}</div>
    <div>{img('mkt_ai_platforms.png')}</div>
  </div>
  <div class="take"><b>The new SEO:</b> {mk['seo_page1_keywords']:,} page-1 keywords drive free traffic, but a
  {mk['ai_share_of_voice']}% share of voice in AI answers is the next battleground — customers increasingly
  ask ChatGPT and Google AI, not just Google Search.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>SEO &amp; AI · 06</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">From data to decisions</span>The Machine-Learning Journey</h2>
  <p style="font-size:12.5px;margin:2px 0 8px">Machine learning here is never a black box or a buzzword — it's a
  disciplined path from a real business question to an action a team can take. Every model in this report walks
  the same five steps, and is graded honestly against a naive baseline.</p>
  {img('ml_journey.png')}
  {img('ml_scorecard.png')}
  <div class="take"><b>How to read the scorecard:</b> a model only earns its place if it beats the baseline
  <i>and</i> drives a decision worth more than the effort. Two honest lessons stand out — the
  <b>delivery predictor barely beats a linear baseline</b> (delivery time is an additive process, so no model
  can do much better; knowing when <i>not</i> to over-engineer is a skill), while <b>no single fraud signal is
  enough</b>, but stacking them lifts a 65%-precision model into a <b>91%-precision review queue</b>. The next
  three pages are the deep-dives — recommendations, correlations, and fraud — each following this same journey.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>THE ML JOURNEY · 07</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">What customers buy together</span>Recommendations</h2>
  {img('rb_recommendations.png')}
  <table><tr><th>Bought together</th><th>Lift</th><th>Confidence</th></tr>{rec_rows}</table>
  <div class="take"><b>{rb['top_rule']}</b> at {rb['top_lift']:.2f}× — cross-sell these pairs on product
  pages and in cart. The highest-ROI output of the whole dataset.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>RECOMMENDATIONS · 07</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">The customer over time</span>Lifetime, Loyalty &amp; Churn</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="v">R{lc['avg_clv']:,}</div><div class="l">Avg lifetime value</div></div>
    <div class="kpi teal"><div class="v">{lc['churn_rate_pct']}%</div><div class="l">Churn rate</div></div>
    <div class="kpi gold"><div class="v">{lc['champions_clv']}%</div><div class="l">CLV from top 10%</div></div>
    <div class="kpi sage"><div class="v">{lc['avg_lifespan_months']}</div><div class="l">Avg lifespan (months)</div></div>
  </div>
  <div class="two-col">
    <div>{img('lifecycle_stages.png')}</div>
    <div>{img('cohort_retention.png')}</div>
  </div>
  <div class="take"><b>The leaky bucket:</b> retention falls from {int(lc['m1_retention'])}% at month 1 to
  {int(lc['m6_retention'])}% by month 6, and the top 10% of customers drive {lc['champions_clv']}% of all
  lifetime value. The <b>{lc['at_risk_customers']:,} "At Risk" customers (R{lc['at_risk_revenue']}m)</b> are the
  single best target for a winback campaign — reachable, valuable, and slipping.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>LIFETIME &amp; CHURN · 08</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">When the world moves the needle</span>External Shock: The 2026 Oil Crisis</h2>
  <p style="font-size:12.5px;margin:2px 0 8px">The <b>{oil['event']}</b> ({oil['event_dates']}) drove Brent crude
  from ~${oil['baseline_brent']} to a peak of <b>${oil['peak_brent']}/bbl (intraday ${oil['peak_intraday']}, +{oil['peak_shock_pct']}%)</b>
  in {oil['peak_month']} — the largest energy-supply disruption since the 1970s. It landed squarely in our window,
  and the business felt it through <b>{oil['crisis_months']}</b> — peaking in March 2026.</p>
  <div class="two-col">
    <div>{img('oil_delivery.png')}</div>
    <div>{img('oil_revenue.png')}</div>
  </div>
  {img('oil_categories.png')}
  <div class="take"><b>Two channels of impact:</b> fuel-linked delivery cost rose to R{oil['peak_delivery_cost']}/order,
  and fuel inflation cut discretionary demand — <b>{oil['worst_category']} fell {oil['worst_category_drop']:.0f}%</b> at peak
  while essentials held. Total over the crisis: ~<b>R{oil['margin_hit']/1e6:.1f}m margin hit</b>
  (R{oil['revenue_lost']/1e6:.1f}m revenue + R{oil['extra_delivery']/1e6:.1f}m delivery). It eased from June as the
  US-Iran deal reopened the strait. <b>The lesson:</b> hedge fuel and lean on resilient essentials when geopolitics
  moves oil. <i>(Business impact modelled on the real Brent price path.)</i></div>
  <div class="footer"><span>KAROO ONLINE</span><span>2026 OIL CRISIS · 09</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">Signals &amp; safety</span>Correlations &amp; Fraud</h2>
  <div class="two-col">
    <div>{img('rb_correlation.png')}</div>
    <div>{img('rb_fraud.png')}</div>
  </div>
  <div class="take"><b>Correlations:</b> metro→faster delivery ({rb['corr_metro_delivery']:+.2f}),
  discount→basket ({rb['corr_discount_qty']:+.2f}), late→returns ({rb['corr_late_return']:+.2f}).
  <b>Fraud:</b> a 2-signal review queue catches {int(rb['review_queue_fraud']/rb['true_fraud']*100)}% of
  fraud at {int(rb['review_queue_fraud']/rb['review_queue']*100)}% precision — a list a team can work daily.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>CORRELATIONS &amp; FRAUD · 10</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">What we do next</span>The Playbook</h2>
  <p style="font-size:12.5px;margin:2px 0 10px"><b>How the data &amp; ML pay back:</b> every action below is
  bought by a specific analysis — recommendations from market-basket ML, budget shifts from ROAS analysis,
  winback from the churn model, fraud savings from the Isolation Forest. Data isn't a report; it's a
  <b>decision engine</b>.</p>
  <div class="val-grid" style="grid-template-columns:1fr 1fr;">
    <div class="val"><div class="t"><span class="q">1</span>Fix availability</div><div class="d">{tk['pct_lead_time']}% is imported — source locally to lift satisfaction.</div></div>
    <div class="val"><div class="t"><span class="q">2</span>Double down on remarketing</div><div class="d">{mk['remarketing_roas']:.0f}× ROAS vs {mk['paid_roas']:.1f}× on cold paid — shift budget.</div></div>
    <div class="val"><div class="t"><span class="q">3</span>Cross-sell proven pairs</div><div class="d">Put {rb['top_rule']} on product &amp; cart pages.</div></div>
    <div class="val"><div class="t"><span class="q">4</span>Speed up the interior</div><div class="d">A regional hub cuts both delivery time and returns.</div></div>
    <div class="val"><div class="t"><span class="q">5</span>Win back "At Risk" customers</div><div class="d">{lc['at_risk_customers']:,} slipping accounts worth R{lc['at_risk_revenue']}m — target before they churn.</div></div>
    <div class="val"><div class="t"><span class="q">6</span>Hedge the discretionary mix</div><div class="d">Oil shocks hit {oil['worst_category']} hardest; lean on resilient essentials when fuel spikes.</div></div>
    <div class="val"><div class="t"><span class="q">7</span>Grow AI visibility</div><div class="d">Push beyond {mk['ai_share_of_voice']}% share of voice in AI answers.</div></div>
    <div class="val"><div class="t"><span class="q">8</span>Run the fraud queue</div><div class="d">{rb['review_queue']:,} accounts, {int(rb['review_queue_fraud']/rb['review_queue']*100)}% precision.</div></div>
  </div>
  <div class="take"><b>The through-line:</b> one governed dataset, turned into decisions across catalogue,
  delivery, marketing and risk. That's <b>The Karoo Way</b> — measured honestly, and acted on.</div>
  <div class="footer"><span>KAROO ONLINE</span><span>PLAYBOOK · 11</span></div>
</div>

<div class="page" style="{pb}">
  <h2><span class="kicker">How it was built</span>Tools &amp; Methodology</h2>
  <table><tr><th>Layer</th><th>Tool</th><th>Role</th></tr>
    <tr><td>Web extraction</td><td>Python scraper</td><td>The 1,000-product marketplace catalogue.</td></tr>
    <tr><td>Infrastructure</td><td>Terraform</td><td>Every AWS resource as code.</td></tr>
    <tr><td>Ingestion</td><td>AWS Lambda</td><td>Serverless data loading.</td></tr>
    <tr><td>Central store</td><td>S3 + Glue Catalog</td><td>One lakehouse — <code>karoo_db</code>.</td></tr>
    <tr><td>ETL / Analytics</td><td>Amazon Athena</td><td>CTAS to Parquet, KPIs, market-basket, correlations.</td></tr>
    <tr><td>Machine learning</td><td>scikit-learn</td><td>Fraud (Isolation Forest), recommendations, correlations.</td></tr>
    <tr><td>Marketing analytics</td><td>Python</td><td>Paid, remarketing, SEO &amp; AI-visibility modelling.</td></tr>
    <tr><td>Visualisation</td><td>matplotlib · Plotly</td><td>Static charts + the interactive province map.</td></tr>
  </table>
  <div class="take"><b>Data journey:</b> extract → S3 raw → Athena curated Parquet → Glue catalogue →
  SQL &amp; ML → this report. One governed source of truth, serverless throughout, every step in code.</div>
  <div class="footer"><span>KAROO ONLINE · ANTHONY APOLLIS</span><span>TOOLS · 12</span></div>
</div>
"""


# web — with sticky nav + download bar + auto-generated section links
NAV_CSS = """
.topnav{position:sticky;top:0;z-index:100;background:#2B2118;display:flex;flex-wrap:wrap;
  align-items:center;gap:2px;padding:0 12px;box-shadow:0 2px 10px rgba(0,0,0,.15);}
.topnav .home{color:#E0A526;font-weight:700;letter-spacing:2px;font-size:13px;padding:12px 10px;text-transform:uppercase;}
.topnav a{color:#e8d5c0;text-decoration:none;font-size:11px;padding:12px 9px;border-bottom:2px solid transparent;transition:.15s;}
.topnav a:hover{color:#fff;border-bottom-color:#C0531F;}
.topnav .dl{margin-left:auto;display:flex;gap:6px;padding:7px 4px;}
.topnav .dl a{background:#C0531F;color:#fff;border-radius:6px;padding:6px 12px;font-weight:600;border:none;}
.topnav .dl a:hover{background:#a5461a;}
html{scroll-behavior:smooth;} .page{scroll-margin-top:56px;} .cover{scroll-margin-top:56px;}
@media print{.topnav{display:none;}}
"""
NAV_SCRIPT = """
<script>
(function(){
  var secs = document.querySelectorAll('.shell > .page, .shell > .cover');
  var nav = document.getElementById('knav');
  secs.forEach(function(sec, i){
    var h2 = sec.querySelector('h2 .kicker') || sec.querySelector('h2') || sec.querySelector('h1');
    var label = sec.classList.contains('cover') ? 'Top' : (h2 ? h2.textContent : 'Section '+i);
    sec.id = 'sec-'+i;
    if(sec.classList.contains('cover') && i>0) return;
    var a = document.createElement('a');
    a.href = '#sec-'+i;
    a.textContent = label.length>22 ? label.slice(0,20)+'…' : label;
    a.title = (sec.querySelector('h2') ? sec.querySelector('h2').textContent.replace(label,'').trim() : label);
    nav.insertBefore(a, nav.querySelector('.dl'));
  });
})();
</script>
"""
web_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Karoo Online — What South Africa Buys Online</title>
<style>{CSS}{NAV_CSS}
body{{background:#f4ece2;}}.shell{{max-width:960px;margin:0 auto;background:white;box-shadow:0 2px 30px rgba(0,0,0,.08);}}
.cover{{min-height:auto;padding:64px 40px;}}.page{{padding:30px 40px;}}
</style></head><body>
<div class="topnav" id="knav">
  <span class="home">Karoo Online</span>
  <div class="dl">
    <a href="reports/Karoo_Online_Data_Story.pdf" download>PDF report</a>
    <a href="reports/Karoo_Online_Data_Story.xlsx" download>Excel</a>
  </div>
</div>
<div class="shell">{body(map_fragment, ts_fragment, web=True)}</div>
{NAV_SCRIPT}
</body></html>"""
(OUT / "index.html").write_text(web_html, encoding="utf-8")
print("Web edition:", OUT / "index.html")

# pdf
pdf_map = f'<div style="text-align:center">{img("sa_choropleth.png")}</div>'
pdf_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}@page{{size:A4;margin:0;}}</style></head><body>{body(pdf_map, "", web=False)}</body></html>"""
(OUT / "Karoo_Online_Data_Story.html").write_text(pdf_html, encoding="utf-8")
pdf = OUT / "Karoo_Online_Data_Story.pdf"
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([edge, "--headless", "--disable-gpu", f"--print-to-pdf={pdf}",
                "--no-pdf-header-footer", str(OUT / "Karoo_Online_Data_Story.html")], check=True, timeout=180)
print("PDF edition:", pdf)

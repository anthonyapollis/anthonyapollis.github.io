"""Multi-purpose interactive SA province map for Karoo Online.
A dropdown switches the visualised metric (revenue, orders, on-time %,
delivery speed, customers). Rich hover on every province."""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

OUT = Path(__file__).parent / "out"
geo = json.loads((OUT / "sa_provinces_simple.geojson").read_text(encoding="utf-8"))
pstats = pd.read_csv(OUT / "province_stats.csv").set_index("province")

DISTRICT_TO_PROV = {
    "City of Johannesburg Metropolitan": "Gauteng", "City of Tshwane Metropolitan": "Gauteng",
    "Ekurhuleni Metropolitan": "Gauteng", "Sedibeng District": "Gauteng", "West Rand District": "Gauteng",
    "Cape Winelands District": "Western Cape", "City of Cape Town": "Western Cape",
    "Central Karoo District": "Western Cape", "Eden District": "Western Cape",
    "Overberg District": "Western Cape", "West Coast District": "Western Cape",
    "Amajuba District": "KwaZulu-Natal", "eThekwini Metropolitan": "KwaZulu-Natal",
    "iLembe District": "KwaZulu-Natal", "Sisonke District": "KwaZulu-Natal", "Ugu District": "KwaZulu-Natal",
    "uMgungundlovu District": "KwaZulu-Natal", "Umkhanyakude District": "KwaZulu-Natal",
    "Umzinyathi District": "KwaZulu-Natal", "Uthukela District": "KwaZulu-Natal",
    "uThungulu District": "KwaZulu-Natal", "Zululand District": "KwaZulu-Natal",
    "Alfred Nzo District": "Eastern Cape", "Amathole District": "Eastern Cape",
    "Buffalo City Metropolitan": "Eastern Cape", "Chris Hani District": "Eastern Cape",
    "Joe Gqabi District": "Eastern Cape", "Nelson Mandela Bay Metropolitan": "Eastern Cape",
    "O.R. Tambo District": "Eastern Cape", "Sarah Baartman District": "Eastern Cape",
    "Fezile Dabi District": "Free State", "Lejweleputswa District": "Free State",
    "Mangaung Metropolitan": "Free State", "Thabo Mofutsanyana District": "Free State",
    "Xhariep District": "Free State",
    "Ehlanzeni District": "Mpumalanga", "Gert Sibande District": "Mpumalanga",
    "Nkangala District": "Mpumalanga",
    "Capricorn District": "Limpopo", "Mopani District": "Limpopo", "Sekhukhune District": "Limpopo",
    "Vhembe District": "Limpopo", "Waterberg District": "Limpopo",
    "Bojanala Platinum District": "North West", "Dr Kenneth Kaunda District": "North West",
    "Dr Ruth Segomotsi Mompati District": "North West", "Ngaka Modiri Molema District": "North West",
    "Frances Baard District": "Northern Cape", "John Taolo Gaetsewe District": "Northern Cape",
    "Namakwa District": "Northern Cape", "Pixley ka Seme District": "Northern Cape",
    "ZF Mgcawu District": "Northern Cape",
}

# per-district record with its province's stats
districts, provs = [], []
for feat in geo["features"]:
    p = DISTRICT_TO_PROV.get(feat["properties"]["name"])
    if not p:
        continue
    feat["id"] = feat["properties"]["name"]
    districts.append(feat["properties"]["name"]); provs.append(p)

def col(metric):
    return [float(pstats.loc[p, metric]) for p in provs]

# derived detail metrics
pstats["rev_per_customer"] = (pstats["revenue"] / pstats["customers"]).round(0)
pstats["orders_per_customer"] = (pstats["orders"] / pstats["customers"]).round(2)

rev = [pstats.loc[p, "revenue"] / 1e6 for p in provs]
orders = [pstats.loc[p, "orders"] for p in provs]
ontime = [pstats.loc[p, "on_time_pct"] for p in provs]
deliv = [pstats.loc[p, "avg_delivery_days"] for p in provs]
custs = [pstats.loc[p, "customers"] for p in provs]
rpc = [pstats.loc[p, "rev_per_customer"] for p in provs]
opc = [pstats.loc[p, "orders_per_customer"] for p in provs]

# rich hover (same for all metrics) — now with per-customer detail
customdata = [[p, f"{pstats.loc[p,'revenue']/1e6:.0f}", f"{int(pstats.loc[p,'orders']):,}",
               f"{int(pstats.loc[p,'customers']):,}", f"{pstats.loc[p,'on_time_pct']:.0f}",
               f"{pstats.loc[p,'avg_delivery_days']:.1f}", pstats.loc[p, "top_category"],
               f"{pstats.loc[p,'revenue_share_pct']:.0f}", f"{pstats.loc[p,'rev_per_customer']:,.0f}",
               f"{pstats.loc[p,'orders_per_customer']:.1f}"] for p in provs]
hover = ("<b>%{customdata[0]}</b><br>"
         "Revenue: R%{customdata[1]}m (%{customdata[7]}% of national)<br>"
         "Orders: %{customdata[2]}  ·  Customers: %{customdata[3]}<br>"
         "Revenue / customer: R%{customdata[8]}<br>"
         "Orders / customer: %{customdata[9]}<br>"
         "On-time: %{customdata[4]}%  ·  Avg delivery: %{customdata[5]} days<br>"
         "Top category: %{customdata[6]}<extra></extra>")

SCALE = [[0, "#FBEFE2"], [0.4, "#E0A526"], [0.75, "#C0531F"], [1, "#7A2E12"]]
SCALE_R = [[0, "#7A2E12"], [0.25, "#C0531F"], [0.6, "#E0A526"], [1, "#FBEFE2"]]

fig = go.Figure(go.Choropleth(
    geojson=geo, locations=districts, z=rev, customdata=customdata, hovertemplate=hover,
    colorscale=SCALE, marker_line_color="white", marker_line_width=0.6,
    colorbar=dict(title="Revenue<br>(Rm)", thickness=14, len=0.7)))

# metric definitions: (label, z, colorscale, colorbar title)
METRICS = [
    ("Revenue (Rm)", rev, SCALE, "Revenue<br>(Rm)"),
    ("Orders", orders, SCALE, "Orders"),
    ("Customers", custs, SCALE, "Customers"),
    ("Revenue / customer (R)", rpc, SCALE, "R / cust"),
    ("Orders / customer", opc, SCALE, "Orders<br>/ cust"),
    ("On-time delivery %", ontime, SCALE, "On-time %"),
    ("Avg delivery days", deliv, SCALE_R, "Delivery<br>days"),
]
buttons = []
for label, z, scale, cbt in METRICS:
    buttons.append(dict(label=label, method="restyle",
                        args=[{"z": [z], "colorscale": [scale], "colorbar.title.text": cbt}]))

fig.update_layout(
    updatemenus=[dict(buttons=buttons, direction="down", x=0.02, y=0.98, xanchor="left",
                      yanchor="top", bgcolor="#FBF3EC", bordercolor="#C0531F", borderwidth=1,
                      font=dict(size=12, color="#2B2118"), pad=dict(t=4, b=4, l=6, r=6))],
    annotations=[dict(text="Show:", x=0.02, y=1.0, xref="paper", yref="paper",
                      showarrow=False, font=dict(size=11, color="#7A4A2B"), xanchor="left")],
    margin=dict(l=0, r=0, t=8, b=0), height=580,
    paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Segoe UI", color="#2B2118"), dragmode="pan")
fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)", projection_type="mercator")

html = fig.to_html(full_html=False, include_plotlyjs="cdn", config={
    "displayModeBar": True, "scrollZoom": True, "displaylogo": False,
    "modeBarButtonsToRemove": ["select2d", "lasso2d"]})
(OUT / "interactive_map_fragment.html").write_text(html, encoding="utf-8")
print("Multi-purpose interactive map written.")
print(f"  metrics: {[m[0] for m in METRICS]}")

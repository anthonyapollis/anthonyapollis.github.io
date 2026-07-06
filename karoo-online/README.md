# Karoo Online — What South Africa Buys Online

An end-to-end data-analytics case study for a South African online marketplace:
a real 1,000-product catalogue, a million-order behavioural dataset, full-spectrum
marketing, and the machine learning that turns them into decisions.

**Open `index.html`** for the interactive report (includes a multi-purpose province map).

## Folder structure

```
Karoo Online/
├── index.html                    ← interactive web report (Netlify-ready)
├── netlify.toml                  ← deploy config
├── reports/
│   ├── Karoo_Online_Data_Story.pdf     ← 12-page print edition
│   ├── Karoo_Online_Data_Story.xlsx    ← 15-sheet insight workbook
│   └── Karoo_Online_Affinity_Graph.pdf ← recommendation-network deep-dive
├── data/                         ← all approved datasets (CSV) + charts (PNG)
└── source/                       ← Python that builds everything (reproducible)
```

## What the report covers

1. **The Karoo Way** — mission, promise, reach
2. **Data provenance** — five sources → one central lakehouse (`karoo_db`) → decisions
3. **The catalogue** — 1,000 real products: price, category, availability
4. **Interactive map** — switch between revenue, orders, on-time %, delivery speed, customers
5. **Paid & remarketing** — spend, revenue, ROAS by channel
6. **SEO & AI visibility** — organic growth, keyword rankings, share-of-voice in AI answers
7. **Recommendations** — market-basket "bought together" pairs
8. **Lifetime, loyalty & churn** — CLV, lifecycle stages, cohort retention
9. **Oil-trade impact** — how a US–Iran oil shock reached delivery cost and demand
10. **Correlations & fraud** — what drives returns + an Isolation-Forest review queue
11. **The playbook** — prioritised, data-driven actions
12. **Tools & methodology** — the full stack and data journey

## Stack

Python web extraction · Terraform · AWS Lambda · Amazon S3 · AWS Glue ·
Amazon Athena · scikit-learn · matplotlib · Plotly

## Data provenance

- **Real:** the 1,000-product catalogue (scraped from Takealot)
- **Modelled (illustrative, benchmarked to SA norms):** the transactional, marketing,
  customer-lifecycle and oil-shock datasets — clearly labelled where they appear

## Deploy

Static site — deploy to Netlify by dragging this folder into the dashboard, or connect
the repository for continuous deployment.

---
© Anthony Apollis · Data & Analytics Engineering

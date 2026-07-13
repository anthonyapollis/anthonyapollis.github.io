# Changelog — Karoo Online

All notable changes to the Karoo Online data-story project. Newest first.
Versioned with git tags (`v1.0`, `v1.1`, …) so any state can be recovered.

## [v1.4.1] — 2026-07-07
### Fixed
- **Time-horizon consistency** — reconciled the framing so the 4-year revenue history
  (Jul 2022 – Jun 2026) and the recent deep-dive analysis window are described coherently,
  removing a stale "18 months" reference in the data-provenance section.

## [v1.4] — 2026-07-07
### Added
- **Guided Machine-Learning Journey** — a walkthrough that takes the reader from a business
  question to a decision through five steps (Ask → Prepare → Train → Validate → Decide), plus a
  **model scorecard** grading all four models (delivery, recommendations, churn, fraud) with
  honest metrics against a naive baseline.

## [v1.3] — 2026-07-06
### Added
- **Data-reconciliation section** — traces one figure (R899) end-to-end (Capture → Collect →
  Land → Transform → Report), with validation gates and the tech that guarantees agreement.
- **GTM demonstration screenshots** — realistic browser-mockup views of the storefront firing
  events and the dataLayer/GA4 inspector.
- **CHANGELOG + version tags** for full change history.
### Fixed
- Cleared orphaned headless-browser processes that were causing slow PDF builds.

## [v1.2] — 2026-07-06
### Added
- **Four years of revenue history** (Jul 2022 – Jun 2026) with an interactive **time-frame
  selector** (1Y / 2Y / 3Y / 4Y + range slider).
- **Sticky navigation bar** and **PDF/Excel download buttons** for easy browsing.
- **Province map expanded to 7 metrics** (added revenue- and orders-per-customer).
- Deployed to **GitHub Pages** at `/karoo-online/` (with `.nojekyll` for fast static builds).
### Changed
- Restored **Takealot** as a named market competitor (AI share-of-voice), while keeping the
  product catalogue de-referenced from any single source.

## [v1.1] — 2026-07-05
### Added
- **Full marketing spectrum**: paid campaigns, remarketing, SEO, and AI-visibility.
- **Customer lifetime, loyalty & churn** (CLV, lifecycle stages, cohort retention).
- **2026 Strait of Hormuz oil-crisis** external-shock analysis (sourced timeline).
### Fixed
- Corrected the oil-shock timeline to the real 2026 crisis (peak ~$120, March 2026).
- Removed marketplace-source references from the catalogue framing.

## [v1.0] — 2026-07-04
### Added
- Initial flagship data story: real 1,000-product catalogue, interactive province map,
  market-basket recommendations, correlations, fraud detection, and a data-provenance view.
- Compact, card-based professional design (interactive HTML + print PDF + Excel workbook).
- End-to-end pipeline: Python extraction · Terraform · AWS Lambda · S3 · Glue · Athena ·
  scikit-learn · matplotlib · Plotly.

---
© Anthony Apollis · Data & Analytics Engineering

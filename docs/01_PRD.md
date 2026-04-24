# Product Requirements Document (PRD)
**Product (working name):** StatForge — an offline, no-code statistical analysis studio
**Document version:** 0.1 (Draft)
**Author:** Product
**Status:** Proposed

---

## 1. Executive Summary

StatForge is a fully offline, no-code desktop application that lets researchers, students, and analysts go from a raw dataset to a publication-quality statistical report without writing a single line of code. Users organize their work into **sessions** (one session = one dataset + its analyses), and every artifact they produce — descriptive summaries, graphs, regression models, model comparisons — is tagged with a unique identity and can be dropped into a **modular report** exported as PDF or HTML.

The product’s core differentiator is the **session → artifact → report** pipeline: nothing the user builds is ever lost, and everything is addressable by ID so the final deliverable is fully user-curated.

---

## 2. Problem Statement

Statistical analysis tools today force users into one of three uncomfortable corners:

- **Code-first tools (R, Python/pandas, Stata):** extremely powerful but require programming literacy and reproducibility discipline most non-technical users don’t have.
- **Cloud GUIs (various SaaS analytics tools):** convenient but require uploading data to the internet, which is a non-starter for regulated data, fieldwork, or low-connectivity environments.
- **Legacy desktop GUIs (SPSS, JMP):** offline but expensive, dated, and their reporting layer is rigid — the user can’t easily curate a custom report from selected artifacts.

There is no well-designed, modern, **offline**, **no-code** tool that treats every analysis step as a reusable artifact and gives the user full control over the final report.

---

## 3. Target Users

**Primary personas:**

- **The Applied Researcher (e.g., biologist, social scientist):** has a dataset, knows the statistical methods they want, but doesn’t want to (or can’t) code. Works with sensitive or unpublished data, so offline is a hard requirement.
- **The Graduate Student:** learning regression and classification methods; wants to try several models, compare them, and hand in a clean report.
- **The Business/Operations Analyst:** comfortable with Excel, intimidated by Python/R, needs rigorous statistical output for internal stakeholders.

**Secondary personas:**

- **The Instructor / TA** demonstrating statistical methods in class.
- **The Consultant** working on client-confidential data on a locked-down machine.

---

## 4. Goals & Non-Goals

**Goals**

- Let a non-programmer complete a full statistical workflow — import, clean, visualize, model, compare, report — end-to-end inside one app.
- Guarantee 100% offline operation: no outbound network calls for core features.
- Make every analysis artifact (graph, model, comparison) durably addressable, so the user can include/exclude each one in the final report on their own terms.
- Persist sessions so a user can close the app and resume exactly where they left off.

**Non-goals (for v1)**

- Real-time collaboration / multi-user editing.
- Cloud sync or account systems.
- Time-series-specific modeling (ARIMA, state-space, etc.).
- Bayesian modeling / MCMC.
- Deep learning.
- Data source connectors beyond flat files (no direct DB or API imports).

---

## 5. Product Scope — Features

Each feature below lists user stories and acceptance criteria. The six feature areas map directly to the sections of the brief.

### 5.1 Data Import & Session Management

**User stories**
- As a user, I can create a named session so I can keep different analyses separated.
- As a user, I can import one dataset (CSV, TSV, XLSX) into a session.
- As a user, I can browse my saved sessions and reopen any of them.
- As a user, I can view my dataset in a paginated spreadsheet with 100 / 200 / 500 rows per page.
- As a user, I can see descriptive statistics (mean, median, std, min, max, quartiles, missing count, unique count, dtype) for every column, and mark individual column summaries for inclusion in the report.

**Acceptance criteria**
- Sessions survive app restart and are listed on a sessions home screen with name, dataset filename, created/modified timestamps.
- The dataset viewer renders 500-row pages on datasets up to 1M rows without UI freeze.
- Descriptive statistics are recomputed lazily and cached; toggling a column’s “Add to report” is idempotent.

### 5.2 Data Preprocessing

**User stories**
- As a user, I can handle missing values per column (drop rows, fill with mean/median/mode, fill with a constant, forward/backward fill).
- As a user, I can standardize (z-score) or normalize (min-max) one or more numeric columns.
- As a user, I can apply transformations to a column and save the result as a **new column** (log, sqrt, reciprocal, Box-Cox, Yeo-Johnson, one-hot encode, label encode, bin/discretize).
- As a user, I can build a **hybrid column** by combining two or more existing columns via +, −, ×, ÷ (and optionally parenthesized expressions of these).
- As a user, I can strip or replace characters in a string column (e.g., remove `$`, `%`, whitespace).
- As a user, I can delete a column.
- As a user, every preprocessing step is logged and reversible within the session (undo stack).

**Acceptance criteria**
- No preprocessing action ever modifies the source file on disk.
- The derived-column pipeline is recorded so the report can reproduce the transformation chain as text (e.g., *“`log_income` = log(`income`)”*).
- Undo restores both the data and the UI state of the affected tab.

### 5.3 Graph View

**User stories**
- As a user, I can plot any seaborn-supported chart type — histogram, KDE, box, violin, strip, swarm, bar, count, point, scatter, line, regplot, residplot, jointplot, pairplot, heatmap, clustermap, lmplot, catplot, ECDF.
- As a user, I can pick the x/y/hue/row/col variables and basic styling (title, palette, figure size) through forms, not code.
- As a user, every plot I create is automatically saved with a unique ID and a human-readable name I can edit.
- As a user, I can see a gallery of all plots in the session and toggle each one for report inclusion.

**Acceptance criteria**
- Each saved plot stores: its ID, name, chart type, parameters (so it can be re-rendered), thumbnail, and full-resolution PNG/SVG.
- Deleting a plot removes it from the gallery and from any report it was included in (with a warning).

### 5.4 Regression & Classification Modeling

**User stories**
- As a user, I can run **linear regression** (OLS), **ridge**, and **lasso** on selected predictors and a numeric target, with optional **interaction terms** chosen from a UI picker.
- As a user, I can run **logistic regression**, **Naïve Bayes** (Gaussian / Multinomial / Bernoulli), **LDA**, and **QDA** on a categorical target.
- As a user, I get the right diagnostics for each family:
  - Regression: coefficient table (with std. error, t, p, CI), R², adj. R², F, RMSE, QQ plot, residual plot, residuals-vs-fitted, scale-location, leverage plot.
  - Classification: confusion matrix, accuracy/precision/recall/F1, ROC curve with AUC (binary), multi-class OVR ROC where applicable, coefficient table where the family has one.
- As a user, I can run a **best-model finder** inside each family (e.g., cross-validated α search for ridge/lasso; subset comparison across classifiers) and see the leaderboard.
- As a user, every fitted model is saved with a unique ID and human-readable name, and can be toggled into the report.

**Acceptance criteria**
- Models are trained on the current state of the session’s data (post-preprocessing).
- Each saved model stores: ID, name, family, formula/spec, hyperparameters, fitted object, metrics, and all diagnostic plots.
- A model can be retrained in one click if the upstream data changes; the old version is preserved unless the user deletes it.

### 5.5 Model Comparisons

**User stories**
- As a user, I can select two or more saved models of compatible types and run a comparison.
- As a user, I can compare nested linear models with **ANOVA** (F-test on residual sums of squares).
- As a user, I can compare non-nested models with information criteria (**AIC**, **BIC**) and cross-validated metrics.
- As a user, I can compare classifiers by metrics table + overlaid ROC curves.
- As a user, every comparison is saved with a unique ID and human-readable name, and can be toggled into the report.

**Acceptance criteria**
- The app prevents incompatible comparisons (e.g., classifier vs. regressor) with a clear explanation.
- The comparison artifact stores both the numeric results and any generated plots.

### 5.6 Reports

**User stories**
- As a user, I can open a **report builder** for a session that lists every artifact in the session (column summaries, plots, models, comparisons) with a checkbox next to each.
- As a user, I can reorder included artifacts and group them into user-named sections (e.g., “Descriptives,” “Diagnostics,” “Final Model”).
- As a user, I can add my own narrative text blocks (plain or lightly formatted) between artifacts.
- As a user, I can export the report as **PDF** and/or **HTML**, both fully self-contained (no external CDN calls).
- As a user, I can save a report layout and re-export it later after tweaking artifacts.

**Acceptance criteria**
- PDF and HTML exports are visually consistent (same section order, same figures, same tables).
- The report is fully modular: removing one artifact does not break the rest.
- Reports generate on a 50-artifact session in under 30 seconds on a modern laptop.

---

## 6. Success Metrics

- **Task success rate:** ≥ 90% of new users complete the reference workflow (import → at least one preprocessing step → one plot → one model → one-page report) unaided in a 20-minute usability test.
- **Session durability:** 0 known cases of lost sessions after clean app shutdown in beta.
- **Performance:** 500-row pagination renders in < 300 ms on a 1M-row dataset.
- **Offline integrity:** static analysis shows no outbound network calls in core modules.
- **Report adoption:** ≥ 70% of sessions that include at least one model also produce at least one exported report.

---

## 7. Assumptions & Constraints

- Users run a supported desktop OS (Windows 10+, macOS 12+, mainstream Linux distros).
- Datasets fit in RAM (v1 does not target out-of-core datasets).
- Users accept that sessions are stored locally and are responsible for their own backups.
- Offline is a **hard** constraint — any future feature requiring the network must be opt-in and clearly flagged.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| User imports a dataset too large for RAM | Detect size at import, warn the user, offer column-subset or row-sample import. |
| Artifact IDs collide across sessions | Use UUIDs, not sequential integers. |
| A model’s fitted object becomes unloadable after an app version upgrade | Version the artifact schema; include migration routines; on failure, keep the metrics/plots and mark the fitted object as “needs refit.” |
| Report generation fails on a single bad artifact and kills the whole export | Render each artifact in an isolated try/except; skip-with-warning rather than abort. |
| Users assume results are reproducible and the app silently changes defaults between versions | Pin library versions in the packaged app; show library versions in the report footer. |

---

## 9. Out of Scope for v1 (Future Candidates)

- Time-series models, Bayesian models, mixed-effects models.
- Database / API / cloud-storage connectors.
- Scriptable “power user” mode (inline Python).
- Collaborative editing and shared sessions.
- Custom plot theming beyond the built-in palettes.
- Multi-dataset sessions / joins.

---

## 10. Release Plan (High-Level)

- **M1 — Foundations:** session management, data import, spreadsheet viewer, descriptive stats, report skeleton.
- **M2 — Preprocessing & Graphs:** full preprocessing suite, seaborn graph library, plot gallery.
- **M3 — Modeling:** regression family (linear/ridge/lasso + diagnostics), classification family (logistic/NB/LDA/QDA + diagnostics), best-model finder.
- **M4 — Comparisons & Reports:** ANOVA/AIC/BIC comparisons, modular report builder, PDF + HTML export.
- **M5 — Hardening & Beta:** large-dataset performance, crash recovery, packaging & signed installers.

---

## 11. Open Questions

- Should preprocessing history be exportable as a standalone “recipe” that can be replayed on a new dataset? (Probably yes, but post-v1.)
- Should the app ship a small set of example datasets for onboarding?
- How deep should the “best model finder” go — a fixed grid, or a configurable search?
- Do we want to support a dark-mode report theme, or is a single print-friendly theme enough for v1?

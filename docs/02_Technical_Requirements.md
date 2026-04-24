# Technical Requirements Document (TRD)
**Product (working name):** StatForge
**Document version:** 0.1 (Draft)
**Status:** Proposed
**Companion to:** PRD v0.1

---

## 1. Purpose & Scope

This document describes how StatForge will be built. It translates the PRD’s product requirements into concrete technical decisions: application architecture, technology stack, data persistence, module responsibilities, performance targets, packaging, and testing. It is scoped to v1 (milestones M1–M5 in the PRD).

---

## 2. Architectural Overview

StatForge is a **single-process desktop application** with a layered architecture. There is no server, no daemon, no network listener. The app is self-contained and ships as an OS-native installer.

The layers are:

1. **UI layer** — widgets, navigation, forms, spreadsheet view, plot canvases, report builder.
2. **Controller / session layer** — orchestrates user actions, manages the undo stack, coordinates calls into the analysis layer.
3. **Analysis layer** — pure-Python modules for preprocessing, plotting, modeling, comparison, and reporting. No UI imports here.
4. **Persistence layer** — SQLite database for session metadata and artifact registry; on-disk parquet/pickle for large binary payloads (datasets, fitted models, rendered plots).
5. **Packaging layer** — bundled Python runtime + pinned dependency set + native installer.

A strict rule: the UI layer never calls pandas/seaborn/scikit-learn/statsmodels directly. It goes through the analysis layer. This keeps the analysis code testable headlessly and keeps the UI thin.

---

## 3. Technology Stack

| Concern | Choice | Rationale |
|---|---|---|
| Language | **Python 3.11+** | Ecosystem fit for the entire analysis stack. |
| GUI framework | **PySide6 (Qt 6)** | Mature, native-looking cross-platform desktop UI with a strong table/spreadsheet widget, thread-safe signaling, and commercial-friendly LGPL license. |
| Data manipulation | **pandas**, **numpy** | Baseline for everything. |
| Statistical modeling | **statsmodels** (OLS, logistic with rich inference; ANOVA), **scikit-learn** (ridge, lasso, NB, LDA, QDA, cross-validation, ROC) | statsmodels gives richer inference tables; scikit-learn gives the classifier bench and the CV machinery. |
| Plotting | **seaborn** (on top of **matplotlib**) | Direct match to the PRD. |
| PDF/HTML reports | **Jinja2** (HTML templating) + **WeasyPrint** (HTML → PDF) | Lets us author one HTML template and get a visually consistent PDF without maintaining two reporting code paths. |
| Local storage | **SQLite** (via `sqlite3` stdlib) for metadata; **parquet** (via `pyarrow`) for datasets; **joblib** for fitted model objects | SQLite is zero-config and reliable; parquet keeps columnar loads fast; joblib is the standard for sklearn model serialization. |
| Packaging | **PyInstaller** (Win/Linux), with OS-native installers (Inno Setup / `.pkg` / `.deb`/`.AppImage`) | Produces single-folder distributions that embed the Python runtime and all dependencies. |
| Logging | Python `logging` module to a per-session rotating file | Helps diagnose user-reported issues without phone-home telemetry. |

**Hard rule on dependencies:** every dependency must work fully offline after install. No package that pulls fonts, tiles, or assets from the network at runtime.

---

## 4. Application Structure

```
statforge/
├── app/
│   ├── main.py                 # entry point; sets up Qt app + main window
│   ├── ui/                     # all Qt widgets, dialogs, views
│   │   ├── sessions_home.py
│   │   ├── data_view.py
│   │   ├── preprocess_view.py
│   │   ├── graph_view.py
│   │   ├── modeling_view.py
│   │   ├── comparison_view.py
│   │   └── report_builder.py
│   ├── controllers/            # mediates UI <-> analysis
│   │   ├── session_controller.py
│   │   ├── data_controller.py
│   │   ├── graph_controller.py
│   │   ├── model_controller.py
│   │   └── report_controller.py
│   ├── analysis/               # pure-python, UI-free
│   │   ├── descriptive.py
│   │   ├── preprocessing.py
│   │   ├── plotting.py
│   │   ├── regression.py
│   │   ├── classification.py
│   │   ├── comparison.py
│   │   └── reporting.py
│   ├── persistence/
│   │   ├── store.py            # SQLite session/artifact registry
│   │   ├── blob_store.py       # file-backed storage for datasets, models, plots
│   │   └── schema.sql
│   └── util/
│       ├── ids.py              # UUID generation
│       ├── undo.py             # command-pattern undo stack
│       └── errors.py
├── resources/
│   ├── templates/              # Jinja2 HTML templates for reports
│   ├── styles/                 # print CSS
│   └── icons/
└── tests/
```

---

## 5. Data Model & Persistence

### 5.1 User data directory

On first launch StatForge creates:

```
<OS user data dir>/StatForge/
├── statforge.db                 # SQLite; sessions + artifact registry
├── sessions/
│   └── <session_uuid>/
│       ├── dataset.parquet      # current state of the dataset (post-preprocessing)
│       ├── dataset_original.parquet
│       ├── plots/<plot_uuid>.png / .svg
│       ├── models/<model_uuid>.joblib
│       ├── models/<model_uuid>.meta.json
│       ├── comparisons/<comparison_uuid>.json
│       └── reports/<report_uuid>.{html,pdf}
└── logs/
```

This split — metadata in SQLite, large blobs on disk — keeps the DB small and fast while letting big artifacts stream from disk only when needed.

### 5.2 SQLite schema (essentials)

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,             -- UUID
  name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  modified_at TEXT NOT NULL,
  source_filename TEXT,
  app_version TEXT
);

CREATE TABLE artifacts (
  id TEXT PRIMARY KEY,             -- UUID
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,              -- 'column_summary' | 'plot' | 'model' | 'comparison'
  name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  spec_json TEXT NOT NULL,         -- parameters needed to regenerate
  metrics_json TEXT,               -- quick-access metrics for UIs
  blob_path TEXT                   -- relative path inside session dir, if any
);

CREATE TABLE preprocess_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  step_index INTEGER NOT NULL,
  op TEXT NOT NULL,                -- 'impute' | 'standardize' | 'transform' | 'hybrid' | 'strip_chars' | 'drop_col' | ...
  params_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE reports (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  layout_json TEXT NOT NULL,       -- ordered list of artifact IDs + narrative blocks
  last_exported_at TEXT
);
```

Every artifact ID is a **UUIDv4**, so IDs are globally unique and the user can share a session directory without collisions.

---

## 6. Module Specifications

### 6.1 Data Import & Spreadsheet View

- **Import:** CSV/TSV via `pandas.read_csv` with an import dialog that previews the first 100 rows and lets the user override delimiter, header row, encoding, and per-column dtype.
- **XLSX** via `openpyxl`.
- **Spreadsheet widget:** Qt `QTableView` backed by a custom `QAbstractTableModel` that pages through the underlying `DataFrame`. Page sizes 100 / 200 / 500. Pagination avoids materializing the full frame into Qt models — only the visible page is copied into the view.
- **Descriptive statistics:** computed on demand per column, cached per (session, column, data_state_hash). Invalidated when preprocessing changes that column.

### 6.2 Preprocessing

Implemented as a **command pattern**: every operation is a `PreprocessStep` object with `apply(df) → df` and `describe() → str`. The controller maintains an ordered list of applied steps; undo pops and replays.

Supported operations:

- Missing values: `drop_rows`, `fill_mean | median | mode | constant | ffill | bfill`.
- Scaling: `standardize` (z-score), `normalize` (min-max).
- Transforms (output as new column): `log`, `sqrt`, `reciprocal`, `boxcox`, `yeo_johnson`, `one_hot_encode`, `label_encode`, `bin_equal_width`, `bin_quantile`.
- Hybrid columns: an expression evaluator limited to column references and the four arithmetic ops + parentheses. No arbitrary Python eval — the expression is parsed with `ast.parse` in `eval` mode and walked with a whitelist visitor that rejects anything other than `Num`, `Name`, `BinOp`, `UnaryOp`, and `Expression`.
- String cleanup: `strip_chars(col, chars)`, `replace(col, pattern, repl)`.
- `drop_column(col)`.

Every operation produces a human-readable description that is stored for the report.

### 6.3 Graph View

- Plots are produced by `analysis/plotting.py`, which maps the user-selected chart type to the corresponding seaborn call.
- Each call runs in a **worker thread** (`QThreadPool`); matplotlib is invoked with the `Agg` backend off the UI thread and the resulting figure is rendered to PNG and SVG in the session blob directory.
- The plot spec (chart type + all parameters) is stored as `spec_json` on the `artifacts` row so the plot can be re-rendered if the user wants a higher-resolution export.
- The gallery is a Qt list view with thumbnails, a checkbox for “include in report,” and inline rename.

### 6.4 Modeling

Two subpackages:

- **regression.py** — wraps `statsmodels.OLS` for OLS (gives the rich inference table the PRD wants), and `sklearn.linear_model.Ridge` / `Lasso` (with `RidgeCV` / `LassoCV` for the best-α finder).
- **classification.py** — wraps `statsmodels.Logit` for the inference-flavored logistic, and `sklearn` for `GaussianNB/MultinomialNB/BernoulliNB`, `LinearDiscriminantAnalysis`, `QuadraticDiscriminantAnalysis`.

**Interaction terms:** implemented by building the design matrix through `patsy.dmatrices` from a formula string the UI assembles from the user’s variable choices (`"y ~ x1 + x2 + x1:x2"`). Works uniformly for the statsmodels and sklearn paths.

**Diagnostics generated for every saved regression model:**
- Coefficient table (coef, std err, t, p, CI 2.5/97.5).
- R², adj. R², F-stat, RMSE, MAE on training data.
- QQ plot, residuals-vs-fitted, scale-location, residuals-vs-leverage.

**Diagnostics generated for every saved classification model:**
- Confusion matrix (counts and row-normalized).
- Accuracy, precision, recall, F1 (per class + macro/weighted).
- ROC curve with AUC (binary) or OVR ROC curves (multiclass).
- Coefficient table where applicable.

**Best-model finder:** for each family, runs a fixed, documented search (e.g., `RidgeCV` across a log-spaced α grid; for the classification side, a cross-validated leaderboard across the available classifier types on the user-selected predictors). Produces its own artifact with the leaderboard table and the winner’s ID.

Every model is persisted with:
- `model.joblib` (the fitted estimator),
- `meta.json` (family, hyperparameters, formula, metrics, diagnostic plot paths),
- an entry in the `artifacts` table.

### 6.5 Comparisons

- **Nested linear models:** `statsmodels.stats.anova.anova_lm` on the two fitted OLS results.
- **Non-nested models / generic:** side-by-side table of AIC, BIC, cross-validated RMSE (regression) or F1/AUC (classification).
- **Classifier comparison:** overlaid ROC curves plotted into one figure.
- Result is saved as a JSON payload + generated plot(s), tagged as a `comparison` artifact.

### 6.6 Reporting

- **Source of truth** is an HTML template rendered by Jinja2. The template iterates the user-selected artifact list and dispatches on `kind`:
  - `column_summary` → a styled `<table>`.
  - `plot` → an `<img>` referencing the saved PNG (embedded as base64 so the HTML is self-contained).
  - `model` → coefficient/metrics table + inline diagnostic plots.
  - `comparison` → comparison table + plots.
  - `narrative` → user-entered HTML (sanitized).
- **PDF export** pipes the same rendered HTML into **WeasyPrint**, which gives us identical layout between HTML and PDF without a second template.
- All assets (images, fonts, CSS) are inlined or embedded so the output files are fully portable and continue to display correctly after being copied or emailed.

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Paginated view of a 1M-row dataset renders in < 300 ms per page. A seaborn plot on 100k rows completes in < 3 s on a modern laptop. Report export for a 50-artifact session completes in < 30 s. |
| **Responsiveness** | No analysis runs on the UI thread. All long-running work uses a `QThreadPool`; the UI shows a cancellable progress indicator. |
| **Offline** | Zero outbound network calls in the packaged app. This is enforced by a CI test that runs the app with network blocked and exercises the main flows. |
| **Portability** | Sessions are self-contained directories. Copying a session directory to another machine running the same or newer app version must work. |
| **Stability** | Crash in one analysis routine must not corrupt the session. All writes go through a “stage-then-rename” pattern for atomicity. |
| **Reproducibility** | The report footer lists the app version and the versions of pandas, numpy, scipy, statsmodels, scikit-learn, and seaborn. |
| **Accessibility** | All forms keyboard-navigable; all charts have a text alternative (the spec string) in the generated report. |
| **Localization (v1)** | English only, but all user-facing strings live in a single `strings.py` to make future i18n straightforward. |

---

## 8. Error Handling & Data Integrity

- All persistence writes are atomic: write to `file.tmp`, `fsync`, then rename. The SQLite store runs in WAL mode.
- If an artifact’s blob is missing on load, the artifact is shown in the UI in a degraded state (“plot missing — re-render?”) rather than silently failing.
- Fitted-model load failures after an app upgrade are caught; the artifact’s metrics and plots are still usable even if the underlying estimator can’t be rehydrated.
- Report generation renders each artifact in an isolated try/except. Failures are logged and inserted into the report as a visible placeholder so the user knows something went wrong.

---

## 9. Packaging & Distribution

- PyInstaller builds single-folder distributions with the Python interpreter embedded.
- Windows: Inno Setup installer, signed.
- macOS: `.pkg` installer, notarized and signed.
- Linux: `.AppImage` as the primary format; `.deb` as a secondary target.
- Auto-update is **explicitly out of scope for v1** (offline-first positioning). Users download a new installer from the vendor and install manually.

---

## 10. Testing Strategy

- **Unit tests** for every analysis module, run headlessly with pytest on fixture datasets.
- **Integration tests** that drive the controllers end-to-end (import → preprocess → plot → model → comparison → report) without touching the Qt UI.
- **UI smoke tests** using `pytest-qt` for the primary views and the report builder.
- **Golden-file tests** for report rendering: committed expected HTML for known inputs; diff-based comparison on CI.
- **Offline enforcement test:** CI job that blocks outbound traffic (iptables / network namespace) and runs the integration test suite; any network attempt fails the build.
- **Performance tests** for pagination and plot rendering, run nightly on representative large datasets.

---

## 11. Security & Privacy

- No telemetry, no analytics, no crash reporting that leaves the machine.
- User datasets never leave the user’s filesystem.
- The hybrid-column expression evaluator is a strict AST allow-list, never `eval()`.
- Narrative text in reports is HTML-escaped before being embedded; only a small allow-list of tags (`b`, `i`, `em`, `strong`, `code`, `p`, `br`, `ul`, `ol`, `li`) is permitted to pass through.

---

## 12. Open Technical Questions

- Is PyInstaller sufficient for macOS universal (arm64 + x86_64) builds, or do we need two separate builds?
- Should the packaged app ship its own fonts for the PDF to guarantee identical rendering across machines? (Likely yes — a libre font like DejaVu.)
- Do we lock WeasyPrint’s GObject/Cairo dependencies inside the bundle, or require system packages? (Preference: bundle them for a true single-installer experience.)
- Is it worth moving heavy model fits into a subprocess (instead of just a worker thread) to isolate memory blowups? (Probably yes for v1.1.)

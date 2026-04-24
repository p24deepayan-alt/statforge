# User Journey Document
**Product (working name):** StatForge
**Document version:** 0.1 (Draft)
**Companion to:** PRD v0.1, TRD v0.1

---

## 1. Purpose

This document describes how real users move through StatForge — from the moment they open the app to the moment they hand in a finished report. It captures personas, the end-to-end journey, and a handful of realistic scenarios, calling out where the user feels friction today and how StatForge is designed to remove it.

The journey is the yardstick the product is measured against: if any of these flows feels clumsy in testing, the feature hasn’t shipped.

---

## 2. Personas

### 2.1 Priya — Applied Researcher
A public-health researcher analyzing household survey data. Comfortable with statistics conceptually, shaky on coding. Handles sensitive data on a work laptop that’s explicitly not allowed to upload to cloud services. Needs a PDF report she can attach to an internal review.

**What she wants:** a tool that respects her data’s confidentiality, gives her proper regression output, and produces a report her supervisor will accept.
**What she fears:** losing her work if the app crashes; having to learn a programming language to get a confusion matrix.

### 2.2 Arjun — Graduate Student
A second-year master’s student in economics taking his first applied econometrics course. Knows R just well enough to copy textbook snippets. Has an assignment due where he must fit linear and regularized models, compare them, and submit a report with diagnostics.

**What he wants:** to fit several models quickly, compare them head-to-head, and turn in a report that doesn’t look like a Jupyter notebook screenshot.
**What he fears:** missing a diagnostic his professor wants because he didn’t know he was supposed to generate it.

### 2.3 Meera — Business Analyst
An ops analyst at a mid-size logistics company. Lives in Excel and PowerPoint. Her VP asked her to understand what drives delivery delays in a dataset of 200k rows. Coding is out of scope; buying another SaaS tool is out of scope; emailing the data to a vendor is out of scope.

**What she wants:** a spreadsheet-shaped tool that does real statistics and produces something she can put in front of her VP without apology.
**What she fears:** being asked to explain a model she doesn’t fully understand and not having the diagnostics to back it up.

---

## 3. The End-to-End Journey (Happy Path)

The six stages below map to the six product areas in the PRD. Every user — regardless of persona — moves through some subset of them.

### Stage 1 — Arrive & orient
The user opens the app and lands on a **Sessions Home** screen listing their previous sessions. A prominent button invites them to create a new session. No login, no onboarding wall, no network prompts.

*Emotional tone:* relief that nothing is being uploaded anywhere; calm.

### Stage 2 — Create a session and import data
The user clicks **New Session**, names it, and is prompted to import a dataset. They pick a CSV from their disk. A preview appears with detected delimiter, header row, and column types; they can override any of these before confirming. Once imported, the session opens with the dataset visible in a spreadsheet view paginated at 100 rows by default, with a dropdown to switch to 200 or 500.

*Friction removed:* no wrestling with `read_csv` kwargs; no “why are all my columns objects?”.

### Stage 3 — Understand the data
The user switches to the **Descriptives** sub-tab. For every column they see dtype, missing count, unique count, and the usual summary statistics. Next to each column summary is an **Add to report** checkbox. The user ticks the summaries they want to show in the final report and moves on.

*Emotional tone:* “I’m being given a head start, not a blank page.”

### Stage 4 — Clean and shape the data
The user moves to the **Preprocessing** tab. They impute missing values in two columns (median for income, mode for region), strip `$` and `,` from a price column, standardize three numeric predictors, log-transform a skewed one (which creates a new `log_income` column automatically), and build a hybrid column `price_per_unit = price / units`. Every step is recorded in a visible history panel; one wrong click is recoverable with **Undo**.

*Friction removed:* no silent in-place mutations; no “wait, which version of the dataset am I looking at?”

### Stage 5 — Explore visually
Over in **Graphs**, the user creates several plots by picking chart type + variables from forms: a histogram of the target, a pairplot of the top predictors, a heatmap of the correlation matrix, a box plot by region. Each plot is saved automatically with an auto-generated name the user can rename (e.g., from *scatter_1* to *delay vs. distance*). The user checks **Include in report** on the two plots they find most telling.

*Emotional tone:* exploratory, almost playful — plots are cheap to make and cheap to discard.

### Stage 6 — Fit models
In the **Modeling** tab the user:

- Fits an **OLS** on `delay ~ distance + weight + region`, including a `distance:region` interaction term chosen from an interaction picker.
- Fits a **ridge** and a **lasso** on the same specification and lets the app’s best-α finder pick the regularization strength via cross-validation.
- Fits a **logistic regression** on a binarized version of the target (late yes/no).
- For good measure, fits **LDA** and **QDA** on the same binary target, and runs the **best-model finder** over the classifier family to get a leaderboard.

For each saved model the user sees the inference table, the relevant diagnostic plots, and an **Include in report** checkbox. They also rename the models (e.g., *ridge_v1_log_income*) so they can find them later.

*Friction removed:* no copy-pasting between libraries, no hunting for the right statsmodels vs. scikit-learn call, no forgetting to generate a residual plot.

### Stage 7 — Compare models
In the **Comparisons** tab the user:

- Picks their OLS with interactions and the nested OLS without and runs an **ANOVA**.
- Picks ridge, lasso, and OLS and gets a side-by-side of AIC / BIC / CV RMSE.
- Picks logistic, LDA, QDA, and Naïve Bayes and gets an overlaid ROC chart plus a metrics table.

Each comparison is saved as an artifact with its own ID, name, and **Include in report** checkbox.

### Stage 8 — Build the report
In the **Report Builder** the user sees every artifact they created in this session, grouped by type. They drag the ones they want into the report outline, organize them into sections (*Descriptives* → *Exploratory graphs* → *Model diagnostics* → *Model comparison* → *Conclusion*), and type short narrative blocks between sections to explain what they’re showing. They hit **Export**, choose PDF + HTML, and get two files in their chosen folder within seconds.

*Emotional tone:* pride. They made this themselves, end to end, without writing code.

### Stage 9 — Return later
A week later they reopen the app. Their session is on the home screen exactly as they left it. They tweak a comparison, add one more model, edit the report layout, and re-export. The old PDF is still there; the new one sits next to it.

---

## 4. Scenario Walkthroughs

### 4.1 Priya — “I need a clean report for review by Friday”

1. Opens StatForge on her work laptop. Sees an empty sessions list.
2. Creates session *Rural Health Survey Q2*. Imports the CSV.
3. In **Descriptives**, ticks the summaries for the five outcome variables.
4. In **Preprocessing**, drops three unusable columns, imputes medians for two continuous variables, creates a `bmi = weight / (height/100)**2` hybrid column.
5. In **Graphs**, makes a KDE of BMI by region and a box plot of blood pressure by age bucket. Adds both to the report.
6. In **Modeling**, fits a linear regression of BP on BMI, age, sex, region, with an `age:region` interaction. Saves it. Runs ridge and lasso; best-α finder chooses ridge.
7. In **Comparisons**, runs ANOVA between the model with and without the interaction term.
8. In **Reports**, arranges everything into four sections, writes two short narrative paragraphs, exports PDF.
9. Emails the PDF to her supervisor. The dataset never left the laptop.

### 4.2 Arjun — “My econometrics assignment is due tonight”

1. Creates a session, imports the assignment dataset.
2. Doesn’t bother with descriptives — goes straight to **Modeling**.
3. Fits OLS, ridge, and lasso on the assigned specification. Ticks all three for the report.
4. Notices the residual plot looks funnel-shaped — goes back to **Preprocessing**, log-transforms the target, refits all three. The old models are still there; he deletes them to keep the report tidy.
5. Runs a model comparison (AIC / BIC / CV RMSE).
6. Builds a report with a short written justification between the before/after models, exports as PDF.
7. Submits. Submission took 45 minutes end to end.

### 4.3 Meera — “What drives delivery delays?”

1. Creates a session with the 200k-row delivery dataset. Pagination keeps the viewer snappy.
2. In **Preprocessing**, strips units from a weight column that was imported as strings, one-hot encodes `region`, standardizes numeric predictors.
3. In **Graphs**, plots delay vs. distance by region (scatter with hue), box plot of delay by carrier, heatmap of predictor correlations. Adds all three.
4. In **Modeling**, fits a logistic regression on *late yes/no*, and an LDA on the same. Runs the classifier best-finder.
5. In **Comparisons**, gets the ROC overlay across classifiers.
6. Builds a report with a narrative tailored for her VP — plain language, chart-first, with the confusion matrix and coefficient table at the end as an appendix. Exports HTML for internal sharing and PDF to attach to a meeting invite.

---

## 5. Journey Map (Emotional Arc)

| Stage | Priya | Arjun | Meera |
|---|---|---|---|
| Open app | Calm | Hurried | Skeptical |
| Import data | Relieved (offline) | Indifferent | Curious |
| Descriptives | Grateful | Skipped | Grateful |
| Preprocessing | Focused | Iterative | Satisfied |
| Graphs | Exploratory | Selective | Exploratory |
| Modeling | Careful | Fast | Confident |
| Comparison | Central | Central | Central |
| Report | Proud | Rushed but relieved | Polished |

The critical emotional moment across all three personas is **building the report**: the payoff for everything before it. The design tax of tagging every artifact with a UUID and an “Add to report” checkbox pays out here.

---

## 6. Pain Points the Product Must Neutralize

- **“Did my work get saved?”** — The sessions home screen and the artifact registry exist so this question is never rational to ask.
- **“Which version of the data am I looking at?”** — The preprocessing history panel is always visible, and the undo stack makes experimentation cheap.
- **“Where did that chart I liked go?”** — Every chart has a UUID and a name and lives in the gallery forever unless the user deletes it.
- **“I can’t remember which alpha I used.”** — Model metadata (hyperparameters, formula, metrics) is stored with the fitted object and rendered in the report.
- **“My supervisor wants a QQ plot and I didn’t make one.”** — Every regression model generates the full diagnostic suite automatically. The user can’t forget because the app didn’t ask.
- **“The exported PDF looks different from the preview.”** — HTML and PDF are generated from the same Jinja template, so what you see is what you get.

---

## 7. Anti-Journeys (what StatForge deliberately does not support in v1)

- A user trying to ingest a live database connection. *(Flat files only.)*
- A user trying to run Bayesian or time-series models. *(Out of scope for v1; a roadmap note appears in the model picker.)*
- A user trying to share a session with a collaborator over a network. *(They can zip and send the session folder; that’s as collaborative as v1 gets.)*
- A user expecting the app to phone home for updates or tips. *(It won’t. Offline means offline.)*

---

## 8. Success Signals from the Journey

The journey is working when, in usability testing:

- Users complete the reference workflow (import → preprocess → plot → model → report) unaided in under 20 minutes.
- Users describe the report builder with phrases like *“it lets me pick what I want,”* not *“it generated something and I couldn’t change it.”*
- Users re-open a week-old session and can resume within 60 seconds.
- When asked whether they trust the output, users point to the diagnostic plots and the version footer in the report rather than saying *“well, it’s a computer, so…”*.

If those four signals are present, the rest of the product is doing its job.

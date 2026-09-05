# Analysis Audit

This is a self-review of the regression analysis in `03_regression_analysis.ipynb`. I went back through every major claim in the notebook and checked it against the data, looking specifically for results that depend on a fragile assumption, interpretations that outrun the evidence, and problems that come from how I built the dataset rather than from the code. The point is intellectual honesty: I want to know which findings are strong, which are fragile, and which need a caveat attached before anyone quotes them.

Nothing here is a bug. The quality audit (`scripts/audit_project.py`) already confirmed the pipeline runs correctly and the data is internally consistent. These are interpretation and specification issues — the kind that professional applied work deals with constantly, and that are worth stating plainly rather than leaving for a reader to discover.

Everything below was produced by re-running the models directly against `data/processed/phillips_curve_panel.csv`.

---

## High severity

### 1. The two-way fixed effects result is only significant because of a three-cluster standard error

**The problem.** The headline positive finding of the project is the two-way fixed effects slope: $\beta_1 = -0.084$, $p = 0.0002$, which I described as a genuine within-state tradeoff surviving the most demanding specification. That p-value comes from standard errors clustered by state. Cluster-robust standard errors are a large-sample tool in the *number of clusters*, not the number of observations, and the conventional threshold is 30 to 50 clusters. **I have three.** With too few clusters the estimator is biased downward, producing standard errors that are too small and t-statistics that are too large.

**The numbers.** The same model, same data, three covariance estimators:

| SE method | β₁ | Std error | t-stat | p-value | Significant at 5%? |
|---|---|---|---|---|---|
| Clustered by state | -0.0843 | 0.0223 | -3.776 | 0.0002 | **Yes** |
| Heteroskedasticity-robust | -0.0843 | 0.0534 | -1.578 | 0.1152 | No |
| Classical (unadjusted) | -0.0843 | 0.0485 | -1.736 | 0.0831 | No |

The clustered standard error is **less than half** the size of the other two. Significance flips entirely on that choice, and the choice that produces it is the one whose assumptions are most clearly violated. The unusually small clustered standard error is the expected symptom of having three clusters, not evidence against the concern.

**What it means for the conclusions.** The project cannot claim a statistically significant within-state Phillips Curve. What it can claim is that the point estimate is negative under every method, stable at about a quarter of the naive bivariate slope, and larger in magnitude than the pooled and state-FE estimates. That is a real result about magnitude and direction. It is not a significance result.

**What I did.** Added Section 4c to notebook 03 reporting all three standard error methods with the cluster-count caveat, and rewrote every place that leaned on the clustered p-value — the Section 4 synthesis, the Newey-West interpretation, Key Finding 4, Key Finding 8, and the clustered standard errors entry in the glossary. The README panel section and limitations now carry the same caveat. The real fix is more clusters: expanding to all 50 states would give roughly 50, which is exactly the threshold the method needs.

### 2. National inflation is nearly the same variable as state inflation, and part of the overlap is mechanical

**The problem.** I described the full model's collapse of the Phillips slope as the result of "adding controls." That is not accurate. One control does all of it — and that control is close to being a copy of the dependent variable.

**The numbers.** Correlation between state inflation and national inflation:

| State | corr(state, national) | Shared variance |
|---|---|---|
| Texas | 0.9414 | 88.6% |
| Massachusetts | 0.9187 | 84.4% |
| Ohio | 0.9658 | 93.3% |

All three exceed 0.90. And dropping *only* national inflation from the full model, keeping oil, the mortgage rate, and the fed funds rate in place:

| State | Simple β₁ | β₁ without national inflation | β₁ full model | R² without | R² full |
|---|---|---|---|---|---|
| Texas | -0.3526 | **-0.3267** (p = 4.5e-05) | -0.0135 (p = 0.66) | 0.2815 | 0.8990 |
| Massachusetts | -0.3478 | **-0.2966** (p = 8.5e-09) | -0.0154 (p = 0.48) | 0.3084 | 0.8820 |
| Ohio | -0.3639 | **-0.4163** (p = 1.8e-12) | +0.0147 (p = 0.46) | 0.3796 | 0.9376 |

Every other control combined leaves the slope essentially at its bivariate value. National inflation on its own drives it to zero.

**Why part of the overlap is mechanical.** State inflation in this project is metro CPI with **Census-region CPI filling every month the metro series does not publish**. The metro series are bimonthly, so roughly **half the monthly observations for Texas and Massachusetts are region-level rather than metro-level**. Regional CPI is a component of national CPI. When I regress state inflation on national inflation, I am partly regressing a series on something that contains it, so the near-1.0 coefficient (1.06 TX, 0.90 MA, 1.08 OH) is not purely an economic finding — some of it is arithmetic.

**What it means for the conclusions.** It does not rescue the naive Phillips Curve; the bivariate slope was still confounded and holding national conditions fixed is still the right instinct. But the full-model null needs restating. It does not show that local labor markets are irrelevant to local prices. It shows that once you condition on a variable 92-97% identical to the dependent variable, almost nothing remains to attribute to anything — including unemployment. The full-model coefficient is a **lower bound** on the local relationship, not a clean estimate of it. This is also the strongest argument for the panel design: time fixed effects absorb national conditions without putting a near-duplicate of the outcome on the right-hand side.

**What I did.** Added Section 3a to notebook 03 with the decomposition table and the data-construction explanation, changed "dominant driver" to "dominant predictor" where the causal reading was not earned, and added the point to Key Finding 2, the README findings section, and the README limitations.

---

## Medium severity

### 3. The `cpi_index` column in the published panel is not a usable price level

**The problem.** The panel CSV carries a `cpi_index` column that alternates between two different index series with different base levels. A real CPI level series moves a fraction of a point per month.

**The numbers.** Mean absolute month-over-month change in `cpi_index`:

| State | Mean abs MoM change | Median | Max | Months jumping >5 points |
|---|---|---|---|---|
| Texas | **18.70** | 17.23 | 42.41 | 316 of 317 |
| Massachusetts | **7.60** | 7.70 | 16.25 | 231 |
| Ohio | **2.36** | 1.90 | 7.83 | 36 |

Texas alternates between roughly 209 and 228 on strict month parity (0.994 consistency) — the Houston metro index and the South region index sitting at different bases, switching every month.

**What it means for the conclusions.** Nothing, as it happens, and this is the important part: `cpi_index` **appears in zero code lines in notebooks 02 and 03**. Notebook 01 computed year-over-year inflation on each source series *independently* and then spliced the **rates**, which is the correct approach and is documented in the code comments. I verified the rate series is clean: mean inflation is nearly identical across the two source bands (TX 2.55 vs 2.40, MA 2.573 vs 2.586, OH 2.40 vs 2.22) and its lag-1 autocorrelation is 0.85-0.93, so there is no month-to-month zig-zag from source switching. Naively differencing `cpi_index` would produce garbage, but nothing in this project does that.

**What should be done.** The column is a trap for anyone who downloads the panel and computes their own inflation rate. It should either be dropped from the exported CSV, split into `cpi_metro` and `cpi_regional`, or renamed to something self-warning like `cpi_index_spliced_do_not_difference`. I have left it in place for now and documented it here and in the README limitations rather than changing the schema mid-project.

### 4. Roughly half of each state's inflation observations are regional, not state-specific

**The problem.** This is the measurement caveat behind findings 2 and 3. Because the metro CPI series are bimonthly, the "state" inflation series is a metro rate in one month and a multi-state Census-region rate in the next. For Texas that means Houston alternating with the entire South region; for Massachusetts, Boston alternating with the Northeast.

**What it means for the conclusions.** Half of the variation I am calling "Texas inflation" is really "South region inflation," which mutes genuine state-specific price movement and inflates the correlation with national inflation. Both effects push the estimated local Phillips relationship **toward zero**, which means my null results are partly a measurement artifact — the true local relationship is probably somewhat stronger than the full model implies.

**What should be done.** Nothing available fixes this with public data; the BLS simply does not publish monthly state-level CPI. The honest move is to state it as a bound on the conclusions, which the README limitations now do.

### 5. Great Recession era estimates rest on 24 observations

**The problem.** The era analysis splits each state's 306 months into four periods, and the Great Recession window is only two years.

**The numbers.** Sample size per state-era cell:

| Era | N per state | β₁ (TX / MA / OH) |
|---|---|---|
| Pre-Crisis (2000-07) | 84 | -0.333 / -0.242 / -0.430 |
| Great Recession (2008-09) | **24** | -1.198 / -1.307 / -1.218 |
| Long Expansion (2010-19) | 120 | +0.249 / +0.018 / +0.258 |
| COVID & Aftermath (2020+) | 78 | -0.715 / -0.386 / -0.569 |

Three of twelve cells fall below 30 observations, and they are the three producing the largest coefficients in the entire project.

**What it means for the conclusions.** The steep recession slopes near -1.2 are the least reliable numbers I report, even though their p-values look excellent — 24 monthly observations spanning a single event cannot separate a structural relationship from one episode. They are also mechanically inflated: during 2008-09 both variables moved violently in opposite directions for one common reason, a collapse in demand, so the regression is partly fitting a single shock.

**What I did.** The notebook already flagged the 24-month issue in the era interpretation, and the README limitations already note it. Both now describe those slopes as suggestive rather than estimates.

---

## Low severity

### 6. Overclaiming language in the notebook prose

I scanned every markdown cell in notebook 03 for five specific patterns. What I found and fixed:

| Pattern | Found | Fix |
|---|---|---|
| Causal verbs where only correlation is shown | "National inflation is the dominant **driver**"; "oil is a significant inflation **driver**" | Changed to "predictor" in both places |
| Temporal claims in a same-month model | "tighter policy is associated with lower **subsequent** inflation" (Section 3 interpretation) | Changed to "lower inflation *in the same month*", noting every regressor is contemporaneous with no lags |
| "Consistently" applied to a result that does not hold | "Massachusetts is **consistently** the flattest"; "its line hugs zero more closely **in every era**" | Both changed to "flattest in three of the four eras" — MA is in fact the *steepest* of the three during the Great Recession (-1.31 vs -1.22 OH, -1.20 TX) |
| Clustered standard errors described as reliable or protective | Four instances (glossary, diagnostics interpretation, Newey-West interpretation, Key Finding 8) | All four rewritten with the three-cluster caveat |
| Central Limit Theorem invoked as a guarantee | "the Central Limit Theorem makes the OLS standard errors and p-values reliable" | Rewritten: large-sample normality assumes near-independent errors, and Ohio's Durbin-Watson of 1.22 says they are not, so the observation count overstates how much comfort the CLT provides |

One further overclaim I found outside those five categories and fixed: Key Finding 7 said oil "only in oil-and-energy-entangled Texas does it visibly bias the Phillips estimate." Texas is the only state whose slope moves *toward* zero when oil is added, but Ohio's moves more in absolute terms (-0.364 to -0.409) with its R² nearly tripling. Oil shifts the estimate in all three states, just in different directions.

The words "always" and "future" also matched my scan but in benign contexts — a grammar convention in the glossary and the "Limitations and Future Research" heading. I left those alone.

### 7. Contemporaneous, linear specification

Every model in the project regresses same-month inflation on same-month unemployment with no lags and no nonlinear terms. Wage bargaining and price resetting take months, and the Phillips Curve is widely argued to steepen at very low unemployment. My specification can detect neither. This is a scope limitation rather than an error, and it was already documented in the notebook and README limitations.

---

## What holds up

Two findings survived everything above, and they are the ones I would defend in a seminar.

**The Texas oil result.** Adding WTI oil prices to the Texas model moves the unemployment slope from -0.3526 to -0.3270 — toward zero, the direction the confounding story predicts — while tripling R² from 0.076 to 0.247. Texas is the only state where the slope attenuates. This finding does not depend on the national inflation problem (oil is not a near-copy of the dependent variable; it is an independent series), does not depend on any standard error choice (the coefficient shift is a point-estimate result), does not use `cpi_index`, and rests on all 306 monthly observations rather than a short sub-window. It is also the finding the project's structural argument predicted in advance, from the energy share of Texas GDP, which makes it a genuine out-of-sample test of the reasoning rather than a pattern found after the fact.

The audit did sharpen it. Oil matters in all three states, not just Texas — Ohio's R² also nearly triples, and its slope *steepens*. The correct statement is that oil is a first-order inflation predictor everywhere, and Texas is the only state where controlling for it pulls the apparent Phillips Curve toward zero, which is exactly the signature of the confounding mechanism.

**Era dependence.** The Phillips slope is moderately negative pre-2008 (-0.24 to -0.43), steeply negative in 2008-09, significantly **positive** during the 2010s in Texas (+0.249) and Ohio (+0.258) with Massachusetts flat (+0.018), and negative again after 2020. The interaction model confirms these are statistically distinguishable, not noise: with Pre-Crisis as the baseline slope of -0.269, all three era interactions are significant (p = 0.009, p < 0.0001, p < 0.0001).

This one is robust for a different reason. It does not rest on a single standard error choice, and the Long Expansion result is the strongest part of it — a *sign flip* on 120 observations per state, far too large a change to be produced by the measurement issues above, which all push estimates toward zero rather than across it. The one caveat is the 24-month Great Recession window; the era-dependence conclusion holds without it, since the Pre-Crisis-to-Long-Expansion contrast alone (84 and 120 observations) carries the finding.

One honest note on the COVID era: the raw sub-period slopes are strongly negative (-0.39 to -0.71), but net of controls the interaction model puts the implied COVID slope near zero (-0.016). The apparent COVID revival is mostly the national inflation surge, not a re-established local labor-market channel. The notebook and README both say so.

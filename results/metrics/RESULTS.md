# Productivity normalization: results

Plan and hypotheses written first: `ranking_project/METRIC_PLAN.md`.
Code: `scripts/approaches.py` (`m1`-`m4`, `b1`, `b2`, sharing the `a1_share` table) and
`scripts/metrics_run.py`; noise floor in `scripts/metric_noise.py`.
Numbers: `results/metrics/*.csv` (copies of `C:/ranking_data/work/*_metric*`).

Setting: IR field, papers born 2006-2014, Δ = 3, authors with ≥3 papers (1,430 on OpenAlex,
1,456 on Semantic Scholar). Outcome = citations in 2018-2022 to papers born ≤ 2017, self-citations
removed, split 1/n across authors.

Metric    | definition
----------|-----------
A1        | Σ_p share(p)/n_authors(p), the current score
M1        | A1 divided by the number of papers published in the range
M2        | median paper share
M3        | mean of the author's 3 best paper shares
M4        | M1 shrunk toward the field mean, k = 3
B1        | per-paper citations (the plain metric)
B2        | number of papers with ≥3 in-window citations

## Table 1 - OpenAlex (the main dataset)

| Metric | ρ future | age bias | top-10 mean | top-100 mean | ties | ρ with paper count | ρ vs A1 | top-100 overlap with A1 |
|---|---|---|---|---|---|---|---|---|
| A1 | 0.708 | -0.178 | 96.5 | 30.5 | 22% | 0.61 | 1.000 | 100 |
| **M1** | 0.625 | -0.185 | 22.3 | 20.4 | 19% | 0.33 | 0.937 | 48 |
| M2 | 0.513 | -0.071 | 7.7 | 13.8 | 82% | - | 0.735 | 31 |
| M3 | 0.692 | -0.183 | 46.3 | 27.8 | 33% | - | 0.969 | 72 |
| M4 | 0.302 | -0.139 | 26.4 | 20.4 | 17% | -0.27 | 0.497 | 48 |
| B1 | 0.646 | -0.080 | 19.8 | 22.3 | 48% | 0.33 | 0.923 | 47 |
| B2 | 0.689 | -0.071 | 85.1 | 32.0 | 98% | - | 0.893 | 79 |

## Table 2 - Semantic Scholar (same papers)

| Metric | ρ future | age bias | top-10 mean | top-100 mean | ties | ρ vs A1 | top-100 overlap |
|---|---|---|---|---|---|---|---|
| A1 | 0.502 | -0.002 | 24.2 | 9.1 | 82% | 1.000 | 100 |
| **M1** | 0.456 | 0.010 | 2.8 | 5.0 | 72% | 0.984 | 53 |
| M2 | 0.126 | 0.090 | 4.1 | 4.5 | 99% | 0.254 | 26 |
| M3 | 0.501 | -0.008 | 21.4 | 9.4 | 89% | 0.995 | 77 |
| M4 | 0.126 | -0.003 | 6.2 | 5.5 | 67% | 0.631 | 56 |
| B1 | 0.457 | 0.089 | 7.7 | 4.8 | 85% | 0.957 | 36 |
| B2 | 0.223 | 0.043 | 22.5 | 7.0 | 100% | 0.278 | 30 |

(Semantic Scholar's numbers are on a much thinner graph - 13,548 edges against 54,351 - so its high
tie fractions and low top-10 values reflect missing edges, not the metric. Its tables are used only to
check whether a finding survives a second source.)

## Noise floor (20 runs dropping 20% of edges; same method as the Δ sensitivity study)

| Metric | ρ with full ranking (min) | median | top-100 overlap (min) |
|---|---|---|---|
| A1 | 0.986 | 0.988 | 93 |
| M1 | 0.980 | 0.983 | 91 |
| M2 | 0.936 | 0.945 | 84 |
| M3 | 0.987 | 0.988 | 91 |
| M4 | 0.984 | 0.986 | 91 |
| B1 | 0.980 | 0.984 | 91 |
| B2 | 0.942 | 0.952 | 90 |

The noise floor here is **much tighter than the 0.03 band fixed in the plan**. So every difference
below is judged against 0.986 (A1's) and against 93 top-100 names, not against 0.03. That makes the
verdicts below stricter than what the plan demanded, not looser.

## Verdicts

**H1 - normalizing lowers age bias. FAILED, in both datasets.**
OpenAlex: age bias goes from -0.178 (A1) to -0.185 (M1); Semantic Scholar: -0.002 to +0.010. Neither is
a move toward zero beyond noise. The dilution effect is real but different: the correlation between
score and paper count falls from 0.61 to 0.33, and the top quintile's mean paper count falls from 13.9
to 9.3. Dividing removes **volume**, not **birth year**. The age bias in A1 is not caused by volume;
it comes from papers born earlier having had longer to collect citations (the same effect H2 of
`ir_sensitivity/metric_hypotheses.md` predicted), and a per-author division cannot touch it.

**H2 - normalization lowers agreement with future impact. HELD.**
ρ future falls 0.708 -> 0.625 on OpenAlex (0.083, ten noise floors) and 0.502 -> 0.456 on Semantic
Scholar. The top-10 mean falls 96.5 -> 22.3. As predicted, dividing promotes authors on few papers:
M1's top 10 has 3-4 papers each against 22-70 for A1's top 10, and the top 100 overlap with A1 is 48.

**H3 - shrinkage recovers the loss. FAILED.**
M4 gives ρ future 0.302, worse than both A1 and M1, and the worst value in the table. With k = 3 and a
3-paper minimum, shrinkage moves the score of every short-record author by a third, which pushes the
ranking toward mid-size records (the M4 top quintile averages 8.1 papers) while adding no accuracy.
The shrinkage constant was fixed in advance at k = 3; a larger k was not tried, so this is a verdict on
this setting, not on shrinkage in general.

**H4 - top-3 mean keeps the best top-10; h-like has the worst ties. HALF HELD.**
M3 keeps ρ future at 0.692 and the highest top-10 mean among per-paper metrics (46.3), and it is the
closest to A1 (ρ 0.969, overlap 72) - it is A1 with the long tail cut. But it does not beat A1, and on
Semantic Scholar its top-10 mean (21.4) is essentially A1's (24.2). B2 does have the worst ties (98%)
and is the least accurate (ρ 0.223) on Semantic Scholar, as predicted, but on OpenAlex it is accurate
(0.689); the prediction held only in the thinner graph.

## The answer to the question that was asked

Dividing the score by the number of papers published **does not improve the ranking** on any measure
the study can check. It removes the volume component (ρ with paper count 0.61 -> 0.33), which is what
it was meant to do, but the cost is accuracy against future impact (-0.083, ten noise floors) and a
top-100 that shares 48 names with A1's. It does not fix age bias, because age bias here is a property
of the birth window, not of output volume.

**M1 agrees with B1 (per-paper citations) almost exactly**: ρ = 0.987 with 84 of 100 top names shared
on OpenAlex (0.978 and 50 on Semantic Scholar). The field-share denominator adds nothing once you
divide by paper count. So the honest reading is: *per-paper average is a different question from total
influence, and the field share only matters when you are adding papers up.*

What this suggests instead, in the order the results point to it:
1. **Keep A1 as the headline** (total, volume included) - it is the most accurate and the most stable.
2. **Report M1 beside it as "per-paper", not as A1's replacement** - the two disagree on half the top
   100, and that disagreement is the interesting part (M1 finds authors A1's long tail buries).
3. **Attack age bias where the evidence points** (the birth window / citation-age gap), not by
   normalizing output. M3 is the only variant that changes the top list without losing accuracy, but it
   changes what is being measured (best papers, not person), so it must be labelled as such.

## Follow-up: the citation deflator (W1/W3)

Plan: `METRIC_PLAN_DEFLATOR.md`; full write-up: `RESULTS_DEFLATOR.md`; numbers
`{ir,irs2}_deflator_{table,agree,moves}.csv`.

D1 (deflated total share) costs almost no accuracy (ρ 0.694 vs A1's 0.708) and barely reorders the
top (97/100 overlap, first nine ranks identical), but it moves age bias the **wrong way**: -0.178 →
-0.217 on OpenAlex, -0.002 → -0.008 on Semantic Scholar. Deflated per-paper counts alone (B1')
are worse (-0.132), so the field share still helps under deflation even though the deflator does
not. Sufficient statistics: 0 of 10,896 in-window edges lose their deflator; the identity test
`D(t)=1` reproduces A1 at ρ = 1.00000000.

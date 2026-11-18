# Metric extension plan 2: citation deflator (W1/W3)

Written **before** any number from the deflated metrics was seen. The M1 plan
(`METRIC_PLAN.md`) is the template; this file fixes the deflator method, then the hypotheses,
then what would count against it.

## Why this metric

`RESULTS.md` records that M1 (per-paper normalisation) **failed H1**: age bias went from -0.178
(A1) to -0.185 (M1), i.e. slightly worse, while accuracy fell 0.708 -> 0.625. The literature
review (`METRIC_LITERATURE_REVIEW.md`, W1/W3) says the reason is that A1 normalises by *field size
within* a 3-year window but not for **citation inflation**: the number of references a paper of a
given age could plausibly attract changes year on year. Petersen et al. (2019, *PNAS*) supply the
standard correction, and it is the highest-value item on the ordered list.

## The method

For a citation received in year `t`, the deflator multiplies it by

    D(t) = R(t0) / R(t)

with `R(t)` the citation supply available in year `t` and `t0` a reference year (we use the first
year of the birth range, so old citations are scaled up to present-day size rather than present
citations scaled down). Applied per edge, so a paper's whole citation history is rescaled.

Equivalent formulation used here, which keeps the citation count an integer where possible:
`share_def(p) = sum_{citations c to p, in window} D(y_citing(c)) / N_F`.

### What `R(t)` is measured on: decision

Two options were considered (put to the user, who chose "continue"):

- **Option A (chosen)**: `R(t)` = **references emitted by papers of year `t` in our pool that point
  OUTSIDE the pool**. Using only outside references is deliberate: if `R(t)` were built from
  in-pool references, it would partly measure our own subset's growth (346k references, 90% of
  which point outside), and the deflator would be circular: it would deflate "our scrape got
  bigger" rather than "IR got bigger".
- **Option B (not used):** true field-wide supply from all CS papers. Not available (requires a
  new full OpenAlex reference crawl over all CS; GCP credits gone). Recorded here so the
  limitation is on record rather than discovered later.

Known residual limitation, stated up front: outside references in our pool are those an IR paper
*did* cite, so they under-represent fields IR stopped citing. That is a bias in `R(t)`'s level,
not in its year-on-year shape, and the shape is all the deflator uses.

### Missing year handling

`R(t)` is undefined before the pool starts (2000) and for years with very few pool papers. Rule:
`R(t)` = references emitted outside-pool per year, computed for every year 2000..2022 from
`ir/works.parquet`, with **no smoothing**; a citation from a year with `R(t)` undefined is dropped
and the paper's `N_F` reduced accordingly. The count of dropped edges is reported.

### Amendment 1 (made after inspecting `R(t)`, before any deflated metric was computed)

Two things were found while building `R(t)`, and they change the estimator. Recorded here rather
than silently applied, because both alter the answer.

**(a) The raw `R(t)` is contaminated by the crawl.** 2001-2003 have 40-54% of papers with <= 4
references (SIGIR and CIKM of those years were scraped with truncated reference lists); 2004 has 23%.
Taking `R(t)` as the raw reference count would deflate citations from 2002 up by ~5x on the strength
of a scraping bug. The reference year `t0` is therefore **2005**, the first year with a clean crawl
(7.9% truncated), and the truncated tail is excluded from the supply estimate. A citation from a year
whose clean supply cannot be estimated is **dropped, not interpolated**.

**(b) The growth in `R(t)` is mostly our crawl getting bigger, not citations getting easier.**
Decomposing (`deflator_Rt_decompose.py`): from 2005 to 2022 papers in the pool grew **x6.6**,
references per paper grew **x2.83**. Total outside references grew x6.0. So 88% of the raw growth
is "we scraped more papers".

This matters because the comparison is between papers of different birth years, and different birth
years have different crawl completeness: a 2006 paper has far fewer pool papers in its citation
window than a 2014 paper. Deflating by raw `R(t)` therefore discounts by *our sampling effort*, which
is not a property of the field.

**Decision, fixing the plan's Option A.** The deflator used is per-citing-paper reference intensity:

    R(t) = (references emitted by pool papers of year t) / (number of pool papers of year t)
    D(t) = R(2021) / R(t)

i.e. **references per paper**, which removes the crawl-size term by construction and leaves the
behavioural part (authors cite more, and more recent work, than they used to). `t0 = 2021` rather
than 2005 because the outcome window is 2018-2022: citations in those years are the ones the ranking
is judged on, so they should carry weight 1 rather than being scaled down by 2.5x.

Three fidelity checks are run and reported alongside:
- `D_naive(t) = raw_refs(t) / raw_refs(t0)` - the deflator as written in the plan and in Petersen,
  unadjusted. Reported to show what the correction is worth, not used as the headline.
- `D_distinct(t)` = distinct outside works cited per pool paper per year. An independent supply
  measure that does not grow with paper count; if `D_distinct` and `D_per_paper` agree, the
  conclusion does not depend on the choice.
- The three curves (`D_total`, `D_outside`, `D_per_paper`) diverge by mean 58-64% in log terms
  (`deflator_Rt_variants.py`), so the choice is **material** and is not a detail. `D_per_paper` is
  the one defended; the others are the sensitivity study.

Known residual limitation, to state in the report, not fix: refs-per-paper measures how many
references a paper *has*, not how many citations each reference *can* absorb. It is a proxy for
supply, not the supply itself. That weakness is why `D_distinct` exists as a cross-check.

## Definitions

For paper `p` born in `y`:

```
c(p)         = # citations to p with y_citing in [y, y+DELTA]
c_def(p)     = sum over those citations of D(y_citing)
share_def(p) = c_def(p) / N_F([y, y+DELTA])
```

Author-level metrics, all with the same `(author, score, n_papers, raw_cites)` shape as A1 and the
same 3-paper minimum, so only one thing differs per row:

- **D1 (deflated total share)**: `sum_p share_def(p) / n_authors(p)`, the direct A1 replacement.
  This is the headline metric.
- **D2 (deflated per-paper share)**: D1 divided by `n_papers`, i.e. M1 with the deflator. This is the
  test of whether the deflator fixes what M1 could not.
- **D3 (deflated + percentile)**: **not in this run.** Percentile scoring is W2/W4 and stays the
  next item; including it here would confound two changes in one row.
- **B1' (deflated raw citations)**: `sum_p c_def(p)/n`, the plain per-paper citation baseline with
  the deflator, carrying no field-share normalisation. Included because if D1 cannot beat B1' it
  is the deflator alone doing the work, and the field-share part is dead weight.

`A1`, `M1`, `B1` are re-run in the same pass on the same `outcome()` so the comparison is exact.

## Evaluation

Unchanged from `METRIC_PLAN.md`: `spearman_future`, `age_bias`, `top10_future_mean`,
`top100_future_mean`, `tie_frac`, `agree(metric, A1)`. Run on **IR (OpenAlex)** first. S2 only if
IR produces a result outside the noise band, to save a run.

The age-bias sign convention is fixed here because it was mis-stated in conversation: `age_bias` is
Spearman rho between **score** and **mean birth year**. Negative = older authors score higher.
A1's -0.178 therefore means A1 favours **older** authors, and a deflator should move this toward 0.

## Hypotheses (stated before the run)

- **H5 (the main claim)** The deflator lowers `|age_bias|` versus A1. Expect `|age_bias(D1)| <
  |age_bias(A1)| = 0.178`, and specifically better than M1's 0.185. This is the hypothesis M1
  failed; if it fails again the "citation inflation" explanation is wrong for this data.
- **H6 (accuracy cost)** The deflator costs less accuracy than M1 did. Expect `spearman_future(D1)`
  in **(0.625, 0.708]**, i.e. above M1, below or equal to A1. Rationale: M1's loss came from
  dividing by a small noisy denominator; the deflator keeps the sum form but rescales old evidence
  down, and old authors are the ones whose citations A1 over-credits.
- **H7 (the deflator is doing the work)** `|age_bias(D1) - age_bias(A1)| > |age_bias(M1) -
  age_bias(A1)| = 0.007`, i.e. the benefit is not the noise band. And `agree(D1, A1)` will show a
  **large** reordering: expect Spearman in 0.80-0.95 and top-100 overlap below 70 of 100, because
  discounting citations by year is a monotone transform on age and must reshuffle old vs new
  authors.
- **H8 (field share survives)** D1 beats B1' on `age_bias` even though both carry the deflator. If
  D1 = B1' (rho > 0.99, as M1 = B1 at 0.987), the field-share normalisation adds nothing under
  deflation and the honest conclusion is: the deflator is the mechanism, the share is decoration.

## What would count against the claim "the deflator fixes the age bias"

- If `|age_bias(D1)| >= |age_bias(A1)|`, H5 fails: the deflator does not fix the problem it was
  built for, and the age bias is not citation inflation but something else (career length, survivor
  bias, popularity of the era's subfield). That is a real finding and would be the next strand.
- If `spearman_future(D1)` falls below 0.625 (below M1), the deflator destroys accuracy and is not
  adoptable as written; the per-year `R(t)` curve would then be the suspect.
- If `|delta age_bias| <= 0.03` (the noise band) and accuracy also does not move, the honest result
  is "the deflator makes no material difference at this scale" and will be reported as such.
- If D1 and B1' tie within the noise band on everything, the field-share normalisation is dead
  weight and D1 should be reported as "the deflator, not the share".
- Noise band: `|delta rho| < 0.03` on n ~ 1,400, per `METRIC_PLAN.md`. The LOO edge-subsample noise
  floor already measured in `ir_metric_noise_summary.csv` is the tighter reference and is reused.

## Steps

1. Compute `R(t)` from `ir/works.parquet`: per citing year `t`, the count of references from
   pool papers of year `t` that do **not** resolve to a pool paper. Write to `results/metrics/ir_R_t.csv`
   together with the in-pool alternative and the papers-per-year denominator, so the curve can be
   inspected before it is used.
2. Implement `c_def` / `share_def` / `d1` / `d2` / `b1p` in `scripts/approaches.py`, reusing
   `a1_share` and adding a `deflated_share` table rather than duplicating the A1 SQL.
3. Add a `--deflator` mode to `scripts/metrics_run.py` that runs A1, M1, B1, D1, D2, B1' in one pass
   and writes `ir_deflator_table.csv` + `ir_deflator_agree.csv`, leaving the existing tables alone.
4. Sanity checks before trusting anything: (a) `R(t)` is monotone-ish non-decreasing, not a spike
   from one bad year of the crawl; (b) the share of edges dropped for undefined `R(t)` is small
   (< 5%); (c) D1 with `D(t) = 1` reproduces A1 exactly (rho = 1.000000) - an identity test.
5. Print the top 10 of D1 next to A1 and name the authors who moved, before writing any
   interpretation.
6. Only then: `RESULTS_DEFLATOR.md`, and deck/report updates.

## AI use and verification

Same as `METRIC_PLAN.md`. Every number is produced by a script kept on disk, so every claim traces
to a CSV column. The identity test in step 4(c) is the check that the implementation is not silently
different from A1. The user checks the top-10 movement in step 5 before the result is described.

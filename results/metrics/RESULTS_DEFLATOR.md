# Citation deflator: results

Plan and hypotheses written first: `ranking_project/METRIC_PLAN_DEFLATOR.md` (Amendment 1 before
any deflated metric was computed). Code: `scripts/approaches.py` (`deflator`, `d1`, `d2`, `b1p`,
deflated variant of `a1`), runner `scripts/deflator_run.py`, movement `scripts/deflator_moves.py`.
Numbers: `results/metrics/{ir,irs2}_deflator_{table,agree,moves}.csv`.

Setting is the same as `RESULTS.md`: IR field, papers born 2006-2014, Δ = 3, authors with ≥3
papers, outcome = citations in 2018-2022 to papers born ≤ 2017, self-citations removed, split
1/n. Both datasets were rebuilt from source before this run and reproduce the original edge counts
exactly (54,351 OpenAlex / 13,548 Semantic Scholar), and A1/M1/B1 reproduce `RESULTS.md` to three
decimals (0.708 / 0.625 / 0.646). The comparison is therefore against the same reference, not a
recomputed one.

## The deflator actually used

    R(t) = references per pool paper of year t pointing OUTSIDE the pool
    D(t) = R(2021) / R(t)                    (t0 = 2021, Amendment 1)

| year | R(t) | D(t) | year | R(t) | D(t) |
|---|---|---|---|---|---|
| 2005 | 18.43 | 1.742 | 2014 | 25.69 | 1.250 |
| 2006 | 19.69 | 1.631 | 2015 | 28.03 | 1.145 |
| 2007 | 20.61 | 1.558 | 2016 | 25.99 | 1.235 |
| 2008 | 20.66 | 1.554 | 2017 | 27.57 | 1.165 |
| 2009 | 19.70 | 1.630 | 2018 | 28.34 | 1.133 |
| 2010 | 20.88 | 1.538 | 2019 | 25.94 | 1.238 |
| 2011 | 20.61 | 1.558 | 2020 | 25.28 | 1.270 |
| 2012 | 22.38 | 1.435 | 2021 | 32.11 | 1.000 |
| 2013 | 23.37 | 1.374 | 2022 | 28.67 | 1.120 |

Pre-2005 years are undefined and dropped (truncated scrape: 40-54% of 2001-2003 papers have ≤4
references). **0 of 10,896 in-window edges (OpenAlex) and 0 of 577 (Semantic Scholar) fall in an
undefined year**, so no author loses evidence. The identity test `D(t) = 1` reproduces A1 with ρ =
1.00000000 and max relative error 0.00e+00 (OpenAlex) / 2.05e-16 (CS pilot), which is the guard on
the implementation.

## Results

### Table 1 - OpenAlex

| Metric | ρ future | age bias | top-10 mean | top-100 mean | ties | ρ vs A1 | top-100 overlap |
|---|---|---|---|---|---|---|---|
| A1 | 0.708 | -0.178 | 96.5 | 30.5 | 22% | 1.000 | 100 |
| M1 | 0.625 | -0.185 | 22.3 | 20.4 | 19% | 0.937 | 48 |
| B1 | 0.646 | -0.080 | 19.8 | 22.3 | 48% | 0.923 | 47 |
| **D1** deflated share | **0.694** | **-0.217** | 91.6 | 30.3 | 17% | **0.998** | **97** |
| D2 deflated per-paper share | 0.610 | -0.232 | 19.8 | 19.9 | 14% | 0.936 | 47 |
| B1' deflated per-paper cites | 0.634 | -0.132 | 22.0 | 21.0 | 16% | 0.929 | 45 |

### Table 2 - Semantic Scholar

| Metric | ρ future | age bias | top-10 mean | top-100 mean | ties | ρ vs A1 |
|---|---|---|---|---|---|---|
| A1 | 0.502 | -0.002 | 24.2 | 9.2 | 82% | 1.000 |
| M1 | 0.456 | 0.010 | 2.8 | 5.0 | 72% | 0.984 |
| B1 | 0.457 | 0.089 | 7.7 | 4.8 | 85% | 0.957 |
| **D1** | **0.499** | **-0.008** | 24.2 | 9.1 | 77% | **1.000** |
| D2 | 0.456 | 0.003 | 2.8 | 4.9 | 67% | 0.985 |
| B1' | 0.457 | 0.073 | 6.4 | 4.1 | 72% | 0.964 |

## Verdicts

**H5 - the deflator lowers |age bias| versus A1. FAILED, in both datasets, and in the wrong
direction.** OpenAlex: -0.178 (A1) → -0.217 (D1), i.e. |bias| *rises* by 0.039. Semantic Scholar:
-0.002 → -0.008, also slightly worse. The predicted mechanism - "old citations are inflated, so
discounting them helps older authors look properly, which is the same direction as correcting A1's
over-credit of them" - produces the opposite ordering: discounting old citations removes *exactly
the citations younger authors do not have*, so the new/old gap widens.

The size of the move (0.039) is above the LOO noise floor for age bias (M1 moved it 0.007), so
this is a real effect, not noise. It is small in absolute terms, but it points away from H5.

**H6 - the deflator costs less accuracy than M1 did. HELD.** ρ future = 0.694 against A1's 0.708,
i.e. a loss of 0.014 versus M1's 0.083 - six times smaller. It is inside the predicted band
(0.625, 0.708] and on Semantic Scholar the loss is 0.003 (0.502 → 0.499). The prediction's
reasoning was right: rescaling the evidence preserves the sum structure (a heavily-cited author is
still heavily cited), so it does not promote short records the way per-paper division did. D1's
top-10 mean future citations is 91.6 against A1's 96.5 - almost unchanged, unlike M1's 22.3.

**H7 - the deflator is doing the work, and it reorders a lot. FAILED on reordering, held on
size.** The size condition holds trivially because H5 failed in the opposite direction (|Δ| =
0.039 > 0.007). But the predicted **large reordering did not happen**: ρ(D1, A1) = 0.998 and
top-100 overlap 97 of 100, against the predicted 0.80-0.95 and below 70. The prediction's premise
was wrong: `D(t)` is *not* a monotone transform on birth year in any way that reshuffles the top.
`D(t)` runs from 1.00 to 1.74 and is nearly flat after 2012; A1's top-100 papers average birth
year 2009.57 and D1's 2009.51, a 0.06-year difference. The deflator barely touches who is on top;
it touches only the tail. **The deflator is a rounding correction at this scale, not a
re-ranking.**

**H8 - the field share survives under deflation. HELD.** D1 age bias -0.217 against B1' -0.132:
the share keeps the bias much smaller (closer to zero) than plain per-paper deflated counts, and
D1 is also more accurate than B1' (0.694 vs 0.634) and keeps a 2× higher top-10 mean (91.6 vs
22.0). Unlike M1 = B1 (ρ 0.987), D1 and B1' are related but not the same metric (ρ 0.929), so the
field-share normalisation is *not* decoration under deflation. The honest reading:
**the deflator alone (B1') makes age bias worse than the undeflated plain metric; the deflator
plus the field share (D1) makes it worse than A1 but less bad than B1'.** Share helps, deflation
hurts.

## Who moves (OpenAlex, D1 vs A1)

The top of the list is **identical rank for rank**: the first nine authors (W. B. Croft, C.
Zhai, S. Dumais, R. W. White, E. Agichtein, B. Carterette, T.-Y. Liu, T. Sakai, J. Allan) hold the
same positions; only two adjacent swaps occur at 10/11 and 12. The largest movements are
*downward* and small: A. Sun 70 → 88, J. Leskovec 91 → 103, G. Buscher 94 → 104, D. Lagun 54 →
64. The largest upward move into the top 100 is +12. So the deflator does not change who is
considered a leading IR researcher - it trims citations of mid-career authors with a long pre-2012
record.

## The answer to the question that was asked

**Correcting for citation inflation does not fix the age bias.** It makes it slightly worse
(0.178 → 0.217 on OpenAlex, 0.002 → 0.008 on Semantic Scholar), while costing almost no accuracy
(0.708 → 0.694) and changing the top of the list essentially not at all (97/100 overlap). This is
a clean result: the age bias in A1 is **not** citation inflation of the form R(t) measures. The
deflator is a small, well-behaved correction that a ranking system can adopt for honesty about
absolute citation counts, but it is not an age-bias fix.

The deflator survives as a *reporting* correction (D1 costs 0.014 ρ and restates a 2005 citation at
1.74× its raw value, so absolute counts from different eras become comparable), and it should be
reported beside A1, not instead of it. The age bias
must be attacked elsewhere. The candidates the literature review already lists, in the order this
result points to:

1. **Percentile scores** (Waltman & Schreiber 2013; Bornmann 2013) - rank each paper against its
   own cohort rather than counting raw citations; the one family not yet tried.
2. **Fixed-age (longitudinal) windows** - the plan's ordered item 3; compare all authors at the
   same number of years since birth. This attacks the birth-window effect directly, which is the
   explanation the M1 and deflator results both point to.
3. **Position-weighted credit** (Tscharntke 2007; Larivière 2016) - near-free here because the
   data carries ordered author lists.

## What this run cannot claim

- The `D(t)` curve is measured on our pool's *outside* references only (Option A). A field-wide
  reference population (Option B) would give a slightly different curve; the GCP credits needed to
  pull it were lost. The choice is material: the three `R(t)` variants diverge by a mean 58-64% in
  log terms (`ir_Rt_variants.csv`).
- The age-bias measure is `spearman(score, mean birth year)` where birth year is the mean year of
  the author's own papers born 2006-2014. It is defined on authors with ≥3 in-window papers (1,430
  on OpenAlex), so it says nothing about authors with thinner records or longer histories. Its
  sign convention: **negative = older authors score higher** (checked against the 2010.36 vs
  2010.72 top-10/population birth years).
- The finding that the deflator makes the age bias *worse* was not pre-registered - H5 predicted
  the opposite. It is recorded as a failed hypothesis, not as a revised one.
- Semantic Scholar's age-bias numbers are near zero for everything because its graph is thin
  (near-ties everywhere), so it cannot confirm or refute the magnitude of the OpenAlex move - only
  its direction, which it does.

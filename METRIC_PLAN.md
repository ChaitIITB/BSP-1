# Metric extension plan: productivity-normalized ranking (M1)

Written **before** any numbers from the new metric were seen, as kell's Way asks.
Everything the plan expects to see, and what would count against it, is fixed here first.

## Goal

Add new author-level metrics derived from the existing field-share metric (Approach 1), starting
with **normalization by output**: the per-paper average rather than the total. Then compare every
metric on the same footing, on the same closed IR dataset, with the same outcome variable.

## Data (fixed, already built)

- `C:\ranking_data\work\ir_edges.parquet` - 54,351 citation edges `(citing, cited, y_cited, y_citing)`
- `C:\ranking_data\work\ir_authors.parquet` - 21,362 (paper, author) rows, 14,266 papers
- `C:\ranking_data\work\ir_citing_authors.parquet` - first authors of citing papers (self-citation filter)
- Field IR, papers born 2006..2014 (BIRTH_MIN..CUTOFF), window DELTA = 3 years
- Semantic Scholar mirror: `work/irs2_*.parquet` (same schema, rebuilt from S2)
- Current results for comparison: `work/ir_eval_table.csv`, `work/irs2_eval_table.csv`

## Definitions

For paper p born in year y:

```
share(p) = #{citations to p with y_citing in [y, y+DELTA]} / N_F([y, y+DELTA])
N_F([y, y+DELTA]) = # citations whose citing paper was born in that window
```

Existing **A1 (total)**: `score_total(a) = (1/n_authors(p)) * sum_p share(p)`  over p with birth in range.

**M1 (productivity-normalized, new)**: `score_avg(a) = score_total(a) / n_papers(a)`.
n_papers counts *all* the author's papers in the birth range (uncited ones add 0, as in A1), and the
3-paper minimum is kept so the denominator cannot be 1.

Corollary metrics to add in the same pass, because they are cheap and diagnose the same thing:

- **M2 (median paper)**: `score_med(a) = median_p share(p)` - robust to one hit paper. Ties are heavy here.
- **M3 (top-k mean)**: `score_top3(a) = mean of the author's 3 best shares` (k = min(3, n_papers)) - the
  "best-work" view; this is the standard bibliometric max/mean-of-top-k family.
- **M4 (shrunk average)**: `score_shrunk(a) = (n*score_avg + k*mu) / (n + k)` with k = 3 and mu the
  field-wide mean share - a denominator that does not collapse on small n.
- **B1 (baseline, per-paper citations)**: `sum_p c(p) / n_papers(p)` - the plain "citations per paper"
  everyone uses; M1 must beat or explain its similarity to this.
- **B2 (baseline, h-index style)**: the count of an author's papers with >= 3 citations in the window.

M2-M4, B1, B2 are included only if M1 raises a question that they answer; they add no new data.

## Evaluation (same as before, no change)

For every metric:
- `spearman_future`: Spearman rho between the metric and the outcome. Outcome = citations in
  [2018, 2022] (self-citations removed, co-author split 1/n) to the author's papers born <= CUTOFF+3.
- `age_bias`: Spearman rho between the metric and the author's mean birth year. 0 = age-neutral.
- `top10_future_mean` / `top100_future_mean`: outcome of the metric's top 10 / 100.
- `tie_frac`: 1 - distinct scores / n, i.e. how much of the list is an arbitrary tie-break.
- `agree(metric, A1)`: Spearman, Kendall, top-100 overlap with the A1 ranking. This is the comparison
  the user asked for: where does each metric reorder people, and who moves up.

## Hypotheses (stated before the run)

- **H1** Averaging (M1) lowers age bias relative to A1, because older authors publish more and a total
  rewards volume. Expect age_bias(M1) > age_bias(A1) (closer to 0) and |age_bias(M1)| < |age_bias(A1)|.
- **H2** Averaging also lowers `spearman_future` versus A1 and versus B1. Averaging rewards one-hit
  authors with a short record, so it should hurt agreement with future impact.
- **H3** Shrinking toward the field mean (M4) recovers most of H2's loss while keeping most of H1's gain.
- **H4** M3 (top-3 mean) keeps the highest `top10_future_mean` of the per-paper metrics; B2 (h-like)
  will have the worst tie fraction of the citation ones and will not beat B1 on spearman_future.

## What would count against the claim "normalization is an improvement"

- If M1's `age_bias` is not closer to 0 than A1's, H1 fails and normalization does not fix the age
  problem it was introduced for.
- If M1 ties with B1 (per-paper citations) on every measure and with A1 on `agree`, then the field
  share carries no information beyond raw per-paper citations, and it should not be kept.
- If M4 fails to restore spearman_future within the sampling noise of A1, the shrinkage form is wrong
  and the naive division is as far as this idea goes.
- **Noise band**: |delta rho| < 0.03 on n ~ 1,400 is treated as no difference. The claim is only made
  for differences above that band.
- If all differences fall inside the band, the honest result is "metric choice does not matter at
  this scale", and that will be reported.

## Benchmarks: do they apply?

Check, not skip. The standard external benchmarks for scholar ranking are the AMiner/Garfield-style
lists (most-influential-entity prediction), the CSRankings venue lists, and CORE venue ranks
(already on disk as `CORE.csv`). None of them is a per-author IR ground truth, and all score
venues, not people. So no external leaderboard can validate these metrics directly.

What the plan uses instead, and why this is not a benchmark:
- the **temporal holdout** (born <= 2014, judged on 2018-2022 citations): the only reproducible
  "ground truth" a citation graph can supply, and it is the same protocol Relay-Linking uses for
  temporal evaluation.
- **CORE venue ranks** (already on disk) as a *secondary* sanity check, reported as concordance
  (fraction of an author's top papers in A/A\* venues) and used only to say "this ranking is not
  absurd", never as a target to optimise.
- the **raw-citation baseline** (B1) as the baseline to beat: any new metric that does not clear it
  on both accuracy and the property it claims (age neutrality, robustness) is not adopted.

`benchmark_skip_reason`: no author-level IR benchmark with a fixed protocol exists; external resources
(CORE ranks) only support a concordance sanity check.

## Steps

1. Implement M1-M4, B1, B2 as functions in `scripts/approaches.py` (same `(author, score, n_papers,
   raw_cites)` return shape as A1), sharing the `a1_share` table so they differ only in aggregation.
2. Extend the `__main__` block to evaluate all metrics with `evaluate()` and add the `agree()` matrix.
3. Run on IR (OpenAlex) and on irs2 (Semantic Scholar). Write `{FIELD}_metric_table.csv` and
   `{FIELD}_agree_matrix.csv` next to the existing tables; keep `{FIELD}_eval_table.csv` unchanged.
4. Report the numbers, then update `progress_update_presentation.html` and `report.html` with the new
   metric results only after they exist.

## AI use and verification

I do the implementation and reading of the numbers. Every number is produced by a script whose output
is kept on disk (`*_metric_table.csv`, logs), so any claim in the deck can be traced to a CSV column.
The user checks: (a) that M1's formula is the division they asked for, (b) that the tie handling in
`evaluate()` is what they expect, (c) the top-10 lists before the deck is shown to the class.

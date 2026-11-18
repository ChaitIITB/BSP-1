# Literature review: complex metrics for ranking people in a field

Written 2026-11-17. Companion to `METRIC_PLAN.md` and `results/metrics/RESULTS.md`.
Scope: what the bibliometrics and science-of-science literature already contains that we have **not**
tried, judged by (a) does it need data we have, (b) does it answer a question we currently cannot answer.

Our data (checked on disk, not assumed): 15,268 works from SIGIR, CIKM, WSDM, TOIS, IRJ, published
2000–2022, with **author names in listed order**, 22.9 references per paper on average, and citation
edges year-stamped 2000–2022. No affiliation, no self-declared field, no abstract for every paper.

---

## 1. The one finding that decides what to do next

Our normalization experiment failed to move age bias, and the literature says why.

**Petersen, Pan, Pammolli & Fortunato, "Methods to account for citation inflation in research
evaluation", Research Policy 48 (2019) 1855–1865.** The key number: the total volume of references
produced per year grows about **5.6% a year and doubles every ~12 years** (their earlier paper, Pan et
al., *J. Informetrics* 12 (2018) 656–678, "The memory of science", gives the growth law). A citation
emitted in 2015 is therefore worth less than a citation emitted in 2003, because there are more of
them. They call this **citation inflation** and propose a **citation deflator**: divide nominal
citations by the publication/reference rate of the citing year, exactly as a currency deflator divides
by a price index. Their result on biology and physics careers: without deflation, the impact of earlier
generations is understated "often by 100% or more of the nominal value"; totals and h-index reorder
substantially once deflated.

**Why this matters to us.** Our A1 denominator `N_F([y, y+Δ])` normalises by the size of the field in
that window. That is a *within-window* normalisation. It scales a paper's citations by how big the
field was while the paper was young — which is not the same as correcting for the fact that a paper
published in 2006 competes for a reference supply that was for ever changing shape. Our age bias
(−0.18 in A1) is plausibly **inflation that our denominator does not deflate**, and that is testable
with data already on disk.

**Concrete test (W1).** Fit the reference-supply curve `R(t) = total citations emitted in year t` from
our own edges, then recompute A1 with each citing-year's contribution scaled by `R(2003)/R(t)`, and
re-measure age bias and ρ against the 2018–2022 outcome. Twenty lines of SQL, only data we have, and a
published method — comparable to Petersen et al. rather than another bespoke variant.

**Preliminary check, run before writing this (so the number is real, not assumed).** Our own IR edges
`R(t)`: 292 in 2003 → 3,039 in 2015 → 4,171 in 2020, i.e. **×10.4 over 2003–2015**. That is *faster*
than the ~5.6%/yr in their corpus (which doubles every ~12 years), so **citation inflation in our
window is large, not marginal** — and our A1 denominator does not touch it. Two caveats that the
full test must respect, and that I have not yet ruled out: (i) part of the rise is our crawl
improving over time, not the field growing, so `R(t)` should be rebuilt as *references per paper ×
papers per year*, the Petersen construction, not raw edge counts; (ii) growth being monotone means a
deflator and a "later is better" trend are confounded, so the deflated ranking must be compared on
both, and only a difference larger than the noise floor reported. So W1 is well-motivated but not yet
a result — the check above says it is worth the run, it does not say the bias will disappear.

The literature is explicit that a fixed window is **not** enough: their Section on balanced counts
shows the top-1% cutoff for a 10-year window rose from ~100 citations (1965 papers) to ~200
(2000 papers). We use Δ = 3. Expect inflation to leak through our window, and measure it.

---

## 2. The standard normalisation family (Waltman), and where A1 sits in it

**Waltman, "A review of the literature on citation impact indicators", *J. Informetrics* 11 (2017)
365–388** (arXiv:1507.02099) and **Waltman & van Eck, "Field normalization of scientometric
indicators", *Springer Handbook of Science and Technology Indicators* (2019)** (arXiv:1801.09985).
These are the reference works; anything we claim about normalisation should be positioned against them.

Two families, and we have only built one of them:

- **Ratio / mean-normalised scores.** `s(p) = c(p) / c̄(field, year)`. Aggregated by **averaging**
  (size-independent: MNCS, FWCI, "category normalised citation impact") or by **summing**
  (size-dependent, "total normalised citation score"). Our A1 is a denominator-variant of the summed
  form, and M1 was our move toward the averaged form — which is why M1 collapsed onto per-paper
  citations: we had reinvented MNCS without knowing it, and MNCS's known weakness (small-n instability,
  one-hit papers) is exactly what H2 and M4 showed.
- **Percentile-based indicators.** Value a paper by its **position in the citation distribution of its
  field and publication year**, not by its count: top 10% / 5% / 1% flags (Tijssen et al. 2002; van
  Leeuwen et al. 2003), or Leydesdorff, Bornmann, Mutz & Opthof (2011) graded classes (below p50 = 1,
  p50–p75 = 2, …), or the "mean percentile rank" (Albarrán, Ortuño & Ruiz-Castillo 2011). The
  celebrated robustness property: percentile indicators are **insensitive to the fat tail**, because
  the 4,000th citation adds nothing after the 1,000th has already made the paper top-1%.

**Why we should build it (W2).** We already compute A3 rounds that use in-cohort percentile and
shrinkage, so the machinery exists. But our A3 r2 used a cohort **within the author's birth year** and
scored 0.582 — it was percentile-based *without the key idea*, which is that the cohort is the **whole
field in that publication year**, not the author's entry class. A paper-level percentile score, summed
or averaged per author, is the standard that reviewers will expect us to have tried.

**Ties are a first-class problem there, and the literature already worked it.** Waltman & Schreiber
(2013), with an empirical comparison in Schreiber (2013), survey threshold-tie handling; our
`evaluate()` averages tied ranks, which is one of the accepted answers but is not the one used in
percentile scoring. Worth stating explicitly which we use and why — the deck currently does not say.

---

## 3. Metrics that need only data on disk, ranked by expected payoff

| # | Metric | Source | Needs | What it would tell us that we cannot say now |
|---|---|---|---|---|
| W3 | **Deflated A1** | Petersen et al. 2019; Pan et al. 2018 | edges + years (have) | Whether the residual age bias is inflation. Highest-value test in this review. |
| W4 | **Paper-percentile score** (PR / MNCS) | Waltman 2017; Bornmann et al. | papers + years (have) | The standard alternative normalisation we have not tried; tail-insensitive. |
| W5 | **g-index, w-index, and h-variants** | Egghe 2006; Wu 2010; reviews: Alonso et al. 2009, Wildgaard et al. 2014 | in-window citation counts (have) | Whether a core-based index beats a sum; h is known to grow with career length, so it should be age-biased — a useful negative control. |
| W6 | **h-rate / m-quotient** | Hirsch 2005 (the `m` parameter); Burrell 2007 | h + years since first paper (have) | The simplest published correction for career length. Cheap baseline for age bias. |
| W7 | **Position-weighted credit** | Vavryčuk, *PLOS ONE* 13 (2018) e0195509; Waltman 2017 §7 | ordered author lists (have) | Whether our uniform 1/n split is distorting the list. IR has heavy first-author ordering (student–advisor), unlike econ/algebra — this is a field-specific check nobody has run on IR. |
| W8 | **Geometric / harmonic / m indices on the h-core** | Egghe; Glänzel & Schubert 2010; Wildgaard et al. 2014 | citation distribution per author (have) | Robust central-tendency of the core, less outlier-driven than g; a concrete answer to M2's tie explosion. |
| W9 | **Eigenfactor-style author score** | Bergstrom, West & Wiseman, *JASIST* 2013 (author-level Eigenfactor on SSRN) | author-author citation matrix (have) | Network position, not receipts. Additive over collectives — a property our A1 does not have. |
| W10 | **PageRank / weighted PageRank on the author co-citation network** | **Ding, *JASIST* 2009** — note this paper is *about IR authors, 108 of them*, so we have a direct precedent to compare top-10 lists against | edges (have) | Ding finds citation rank correlates highly with PageRank across all damping factors, and **neither correlates with centrality measures**. We can check if that holds on our larger graph. |
| W11 | **Citation-age / windowed-at-fixed-age score** | Pan et al. 2018; Petersen et al. 2019 (fixed-Δ window) | edges with years (have) | Scores every paper at *, say, 5 or 10 years after birth, so no paper is favoured by having had longer. We currently score at Δ=3 only and never tested whether age bias is a window artefact — this is the direct test. |
| W12 | **Disruption / novelty (CD index)** | Funk & Owen-Smith, *ASQ* 2017 (CD index); Wu, Wang & Evans, *Nature* 566 (2019) | references + citers (have) | Whether "influential" and "field-changing" are the same people. Not a ranking metric on its own, but the most interesting *additional dimension* on the list. |

Beyond these, three other well-known families exist and each needs data we either have partly or not at all:

- **Q-factor and the SJR-style prestige family** (Bollen et al. 2006; González-Pereira et al. 2010):
  need a two-level prestige iteration; doable on our edges, but overlaps W9/W10 enough that I would not
  build it separately.
- **RCR / relative citation ratio** (Hutchins et al., *PLOS Biology* 2016): the NIH version of
  field-and-year normalised citation; its distinguishing feature is that the expected citation count is
  estimated from the paper's own **co-citation network**, not from a venue label. Interesting because
  we *have* refs, but it needs a full-graph pull, not our closed IR subset, to fit the co-citation model.
- **Citation-graph embeddings** (node2vec, metapath2vec, author embeddings; e.g. "Author ranking on
  heterogeneous academic networks"): all need a much larger graph than a 5-venue closed subset, else
  embeddings mostly learn venue identity. Functionally covered by W9/W10 at our scale.

---

## 4. Counting credit — a live methodological objection to A1

Two reviews make a point we should pre-empt rather than discover in the room:

- **Waltman 2017 §7** and **Vavryčuk 2018** both argue **full counting** (every co-author gets the
  whole credit) is unfair and inflates productivity for multi-author fields, while **fractional**
  counting removes discipline differences. Our 1/n split is the standard fractional scheme — good.
- But Vavryčuk shows the *ordering* of the co-author list carries the signal, and proposes
  **author-position weighting** (roughly first/last > middle). IR is the canonical case: single-student
  advisor papers are common, and a three-letter CIKM paper with five authors is not five people's work.
- Also from Waltman: **self-citations** and **review articles** should be handled explicitly. We do
  remove self-citations in the outcome but our in-window score keeps them.

**W7 is therefore cheap and novel for IR specifically**: re-run A1 with position-weighted credit and
measure both the reordering and whether the IR-vs-general-science claim holds. No IR paper that I found
does this on a closed IR graph.

---

## 5. What this means for the project's story

The slides currently say "we tried normalisation by output; it does not fix age bias; the fix is in the
birth window." **The literature makes that last clause a specific, published, testable proposal**
(Petersen et al.'s deflator), not a hand-wave. That upgrades the deck from "we tried a thing" to
"we tried the naive fix, the literature says the right fix is a citation deflator, here it is measured".

Three claims I would now make in the deck, each backed by a citation:

1. M1 is **MNCS** (Waltman & van Eck 2019) rediscovered, and its failure mode is the documented one.
2. Age bias is very likely **citation inflation** (Petersen et al. 2019), testable in one run (W1).
3. The remaining unexplored standard family is **percentile-based** indicators (Waltman 2017), where
   our ties problem is also a documented one (Waltman & Schreiber 2013).

---

## 6. Proposed order of work

1. **W1/W3 deflator** — highest value, smallest change, published method, directly attacks the open
   problem. One run, two numbers (age bias, ρ future).
2. **W4 percentile score** — the missing standard; reuses A3's percentile machinery.
3. **W11 fixed-age window** — the arbitrating test between "age bias is the window" and "age bias is
   inflation".
4. **W7 position weight** — cheap, IR-specific, rhetorically strong at a CS venue.
5. **W10 PageRank** — compare against Ding (2009)'s published top authors for IR; a rare chance at an
   external sanity check with named people.
6. W5/W6/W8 as one combined "core indices" block, mostly as negative controls (h *should* be the most
   age-biased; if it is not, something is wrong with our evaluation).

---

## 7. Bibliography

- Albarrán, P., Ortuño, I., Ruiz-Castillo, J. (2011). High- and low-impact citation measures: Empirical applications. *J. Informetrics* 5, 122–145.
- Alonso, S., Cabrerizo, F., Herrera-Viedma, E., Herrera, F. (2009). h-index: A review focused on its variants, computation and standardization. *J. Informetrics* 3, 273–289.
- Bergstrom, C. T., West, J. D., Wiseman, M. A. (2008/2013). The Eigenfactor metrics. *J. Neuroscience* 28, 11433; author-level extension in *JASIST* (2013).
- Bollen, J., Rodriguez, M. A., Van de Sompel, H. (2006). Journal status. *Scientometrics* 69, 669–687.
- Bornmann, L., Marx, W. (2015). Methods for the generation of normalized citation impact scores. *J. Informetrics* 9, 408–418.
- Burrell, Q. L. (2007). On the h-index, the size of the Hirsch core and Jin's A-index. *J. Informetrics* 1, 170–177.
- Ding, Y. (2009). PageRank for ranking authors in co-citation networks. *JASIST* 60, 2229–2243.
- Egghe, L. (2006). Theory and practice of the g-index. *Scientometrics* 69, 131–152.
- Funk, R. J., Owen-Smith, J. (2017). A dynamic network measure of technological change. *ASQ* 62, 791–823.
- Glänzel, W., Schubert, A. (2010). Hirsch-type characteristics of the tail of distributions: The generalized h-index. *J. Informetrics* 4, 493–504.
- González-Pereira, B., Guerrero-Bote, V. P., de Moya-Anegón, F. (2010). A new approach to the metric of journals' scientific prestige: The SJR indicator. *J. Informetrics* 4, 379–391.
- Hirsch, J. E. (2005). An index to quantify an individual's scientific research output. *PNAS* 102, 16569–16572.
- Hutchins, B. I., Yuan, X., Anderson, J. M., Santangelo, G. M. (2016). Relative Citation Ratio (RCR). *PLOS Biology* 14, e1002541.
- Leydesdorff, L., Bornmann, L., Mutz, R., Opthof, T. (2011). Turning the tables on citation analysis: the top-10 approach. *JASIST* 62, 1370–1379.
- Mingers, J., Leydesdorff, L. (2015). A review of theory and practice in scientometrics. *EJOR* 246, 1–19 (arXiv:1501.05462).
- Pan, R. K., Petersen, A. M., Pammolli, F., Fortunato, S. (2018). The memory of science: Inflation, myopia, and the knowledge network. *J. Informetrics* 12, 656–678.
- Petersen, A. M., Pan, R. K., Pammolli, F., Fortunato, S. (2019). Methods to account for citation inflation in research evaluation. *Research Policy* 48, 1855–1865.
- Radicchi, F., Fortunato, S., Castellano, C. (2008). Universality of citation distributions. *PNAS* 105, 17268–17272.
- Schreiber, M. (2013). How to calculate the practical significance of citation impact differences? *Scientometrics*.
- Tijssen, R. J. W., Visser, M. S., van Leeuwen, T. N. (2002). Benchmarking international scientific excellence. *Research Evaluation* 11, 27–43.
- van Leeuwen, T. N., Visser, M. S., Moed, H. F., Nederhof, A. J., van Raan, A. F. J. (2003). The Holy Grail of science policy. *Scientometrics* 57, 257–280.
- Vavryčuk, V. (2018). Fair ranking of researchers and research teams. *PLOS ONE* 13, e0195509.
- Waltman, L. (2016/2017). A review of the literature on citation impact indicators. *J. Informetrics* 11, 365–388 (arXiv:1507.02099).
- Waltman, L., Schreiber, M. (2013). On the calculation of percentile-based bibliometric indicators. *JASIST* 64, 372–379.
- Waltman, L., van Eck, N. J. (2013). A systematic empirical comparison of different approaches for normalising citation impact at the paper level. *J. Informetrics* 7, 833–849.
- Waltman, L., van Eck, N. J. (2019). Field normalization of scientometric indicators. In *Springer Handbook of Science and Technology Indicators* (arXiv:1801.09985).
- Wildgaard, L., Schneider, J. W., Larsen, B. (2014). A review of the characteristics of 108 author-level bibliometric indicators. *Scientometrics* 101, 125–158.
- Wu, L., Wang, D., Evans, J. A. (2019). Large teams develop and small teams disrupt science and technology. *Nature* 566, 378–382.
- Wu, Q. (2010). The w-index: A measure to assess scientific impact by focusing on widely cited papers. *JASIST* 61, 609–614.

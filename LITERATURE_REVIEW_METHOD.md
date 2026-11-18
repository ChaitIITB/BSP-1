# How to run the literature review for this project

Written after the deflator strand closed. It has three parts: (1) the *method* for running the
review so it is defensible and reproducible, (2) the *terms* to search with, (3) the *research
areas* to search in. Part 4 is the concrete plan for the next metric (fixed-age window).

Sources were found with Exa searches; the queries are listed at the end so the search itself is
auditable.

---

## 1. The method

The project has two literature jobs that are being done with one habit (free-text web search),
and they need different methods.

### Job A — "what is the standard fix for bias X?" (the metric review)

This is what produced `METRIC_LITERATURE_REVIEW.md` and the deflator plan. The risk here is not
finding papers; it is **stopping when a plausible-sounding paper turns up**. The fix used so far
is the right one and should become the rule:

1. Search the *name of the failure*, not the name of the solution ("age bias citation indicators",
   not "deflator").
2. Check whether the paper you found *pre-defines* the bias you are measuring, and if so copy its
   definition verbatim into the plan before computing anything. (Petersen et al. 2019 supplied the
   deflator; Waltman & van Eck 2019 pre-defined MNCS's small-n failure, which is what H2/H4
   reproduced.)
3. Write the hypothesis and its falsifier into `METRIC_PLAN*.md` **before** running. Both existing
   plans do this and it is what made "H5 FAILED" a usable result rather than a story.

### Job B — "is my review complete?" (coverage)

The standard instrument for this is a **systematic-review protocol**, and the two documents that
matter are:

- **PRISMA 2020** — the reporting checklist and the flow diagram. The flow diagram is the useful
  part: it forces you to count records *identified → screened → included*, so an incompleteness gap
  is visible as a number instead of being invisible.
- **TARCiS** (Hirt et al., *BMJ* 2024, bmj-2023-078384) — a statement specifically on **citation
  searching**, i.e. exactly the backward/forward "snowballing" this project already does informally
  every time it follows a paper's references or citing papers. Its recommendations you should adopt
  as written:
  - use **"citation searching"** as the umbrella term; **backward citation searching** for
    retrieving cited references, **forward citation searching** for retrieving citing papers;
  - seed from **all included records of the primary search**, not from one convenient paper — the
    deflator strand did seed from one author's prior work once, and that is the failure mode TARCiS
    rec. 4 names;
  - where the topic is hard to search for by keyword (mine is: "how to rank researchers under
    citation inflation"), backward + forward citation searching should be **seriously considered as
    supplementary search**, not optional;
  - prefer a citation index over manually reading reference lists (rec. 5), and consider **two
    citation indexes** for coverage (rec. 6) — for this project that means OpenAlex *and* Semantic
    Scholar, which is already done for data but not for the review.

Evidence that snowballing is worth the effort: Badampudi, Wohlin & Petersen (2015) found
snowballing found 83% of the papers in their study versus 46% for a database search — but the
reliability **depends entirely on the start set**. That is a direct argument for TARCiS rec. 4.

### Practical workflow to adopt

For the next metric (and any later one):

1. **Seed set**: take the papers already cited in `METRIC_LITERATURE_REVIEW.md` plus every paper
   named in `RESULTS*.md`. That is the "all included records" TARCiS asks for.
2. **Backward**: screen titles/abstracts of their references (OpenAlex `referenced_works` is
   already ingested in `C:/ranking_data` — no new crawl needed).
3. **Forward**: screen the papers citing them. This does need a new pull; cost is small for
   ~20 seeds.
4. **Keyword pass** with the terms in section 2, restricted to the areas in section 3.
5. **Stop rule**: record the round at which a new round adds nothing new (the "iterative citation
   searching" termination). Write the round number in the plan.
6. **Log**: counts for a PRISMA-style flow line: `identified N → screened M → included K`.

---

## 2. Terms (use these exact phrases; the plain-English ones return noise)

Names that are established in the literature and should replace the informal ones the project has
been using:

| What the project calls it | Term to search |
| --- | --- |
| following references / citing papers | **backward / forward citation searching**, **snowballing** (BSB/FSB), **iterative citation searching** |
| "older authors score higher" | **age bias**, **academic age**, **career age**, **time-in-field**, **exposure**, **citation window** |
| "citations got cheaper / the field inflated" | **citation inflation**, **reference growth**, **citation density**, **citation deflator** (Petersen et al.) |
| "the metric favours people who publish more" | **productivity bias**, **size dependence**, **size-independent indicators** |
| "the leaders don't move but the middle does" | **rank stability**, **rank reversals**, **indicator robustness**, **sensitivity analysis (perturbation)** |
| "papers in different subfields can't be compared" | **field normalisation**, **field classification**, **MNCS / field-weighted citation impact (FWCI)**, **percentile-based indicators** |
| "one paper carries the author" | **small-n instability**, **single-hit / one-hit papers**, **tail dependence** |
| "splitting credit between co-authors" | **fractional counting**, **author-level normalisation**, **full vs fractional counting** |
| "the author may be two people" | **author name disambiguation**, **homonyms / synonym author records** |
| "why do a few authors dominate" | **cumulative advantage**, **preferential attachment**, **Matthew effect** |
| "the score should mean *in top X%*" | **percentile rank classes (PR6/PR8)**, **top 10% share**, **excellence indicators** |
| "not just how many, but who cites you" | **position-weighted citation impact**, **PageRank (Pagerank / PageRankCite)**, **network centrality** |

---

## 3. Research areas to search in

In rough order of usefulness to this project:

1. **Bibliometrics / scientometrics** — the home field. Journals: *Scientometrics*, *Journal of
   Informetrics*, *Quantitative Science Studies*, *Research Evaluation*. This is where the
   author-level indicators, the deflator, percentile indicators and stability work all live.
2. **Research assessment / responsible metrics** — **ISSI**, **DORA**, **Leiden Manifesto**, and
   the Waltman/"Scientometrics of scientometrics" strand. Relevant because it states *which* biases
   are considered disqualifying, which is the normative backdrop for the hypotheses.
3. **Computer science education / CS ranking** — CSRankings, and the "which ranking is fair"
   literature. Directly relevant: the project's A1 is essentially a CSRankings-style field-share.
4. **Systematic-review methodology** — PRISMA, TARCiS, snowballing (software-engineering version:
   Wohlin 2014; Badampudi 2015). This is *for the review itself*, not for the metric.
5. **Network science** — PageRank on citation graphs, preferential attachment, burstiness. Relevant
   only for the last untried metric family (Pagerank).
6. **Name disambiguation / data quality** — relevant if the residual 0.05 drop in accuracy on
   Semantic Scholar is attributed to matching, which it partly is.

Searches to *avoid*: general "how to rank scientists" web queries. They return opinion pieces and
university news. Always search the named-term column above.

---

## 4. What this means for the next metric

The literature points at one specific gap and one specific untried standard family:

- **Fixed-age window** — the deflator result (H5 failed, H6 held) says citations are mostly stable
  under reshuffling of *when* they arrive; what is not fixed is *how much time* each paper has had.
  Every paper should be scored over the same number of years since birth, not the same calendar
  window. This is what the literature calls fixing the **citation window / academic age**.
- **Percentile scores** — the standard untried family. Instead of summing normalised citations,
  convert each paper to "top X% of its field-year" and average. This is the family that replaces
  the small-n instability of MNCS (which is what M1 rediscovered) and is the family CSRankings-adjacent
  work uses.

Recommended order: fixed-age window first (clearest prior, cheapest to compute from existing
tables), then percentile score.

---

## 5. Sources

- Hirt J. et al. **TARCiS statement: guidance on terminology, conduct and reporting of citation
  searching.** *BMJ* 2024;385:e078384. https://www.bmj.com/content/385/bmj-2023-078384
- Page M.J. et al. **PRISMA 2020 statement.** *BMJ* 2021;372:n71.
- Badampudi D., Wohlin C., Petersen K. **Experiences from using snowballing and database searches
  in systematic literature studies.** EASE 2015. doi:10.1145/2745802.2745818
- Wohlin C. **Guidelines for snowballing in systematic literature studies.** EASE 2014;
  Wohlin & Prikladnicki. *Database searches vs. snowballing*, ESEM 2013.
  https://www.wohlin.eu/esem12a.pdf
- Petersen A.M. et al. **A quantitative model of citation growth.** *PNAS* 2019 — source of the
  deflator used in `METRIC_PLAN_DEFLATOR.md`.
- Ioannidis J.P.A., Boyack K., Wouters P.F. **Citation metrics: a primer on how (not) to
  normalize.** *PLOS Biology* 2016;14(9):e1002542. States the year-normalisation failure that the
  deflator was meant to fix.
- Waltman L., van Eck N.J. **Field-normalised citation indicators: a review.** *Journal of
  Informetrics* 2019 — MNCS and its documented failure modes.
- Waltman L. et al. **The Leiden Manifesto for research metrics.** *Nature* 2015.
- Weber I. et al. **The stability of the h-index under perturbations** (10/25/50% random removal;
  ≥95% pairwise agreement at 10% removal). Used as the comparison for the project's own noise floor
  (20 runs × 20% edge drops, A1 ρ moves ≤ 0.014).
- Győrffy B. et al. **A global interdisciplinary platform for academic age-normalised researcher
  evaluation.** *Scientometrics* 2026. doi:10.1007/s11192-026-05608-y — states explicitly that
  raw citation metrics favour older researchers; the academic-age normalisation baseline.

## 6. The Exa queries used (so the review is reproducible)

1. "TARCiS statement citation searching snowballing literature review reporting guideline"
2. "systematic review snowballing Wohlin guidelines forward backward citation chasing"
3. "author-level citation indicators age bias academic age exposure normalization cumulative
   advantage reviewer"
4. "responsible metrics rank stability sensitivity perturbation bibliometric indicator robustness"

Earlier rounds (already reflected in `METRIC_LITERATURE_REVIEW.md`): metric families W1–W12,
field classification/normalisation, author name disambiguation, citation/paper-removal robustness,
ISSI 2025 responsible-metrics work.

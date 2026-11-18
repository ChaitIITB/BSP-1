# Hypotheses about Approach 1's score: what it actually measures
### written 2026-11-16, BEFORE any of the confirmatory runs below

Data: OpenAlex IR graph — 14,462 papers (SIGIR 5,370 · CIKM 7,009 · WSDM 1,458 · TOIS 812 · IRJ 619),
54,351 in-set citation edges, 1,430 authors with ≥3 in-window papers.
Approach 1 (A1) as in `scripts/approaches.py`: delta = 3, cutoff = 2014, birth_min = 2006, min_papers = 3,
`score(author) = Σ_{papers p of author} share(p) / n_authors(p)` where `share(p)` is p's citations in
[y_p, y_p+3] divided by the field's total citations in that window.

**Why this document.** The previous sensitivity study asked whether A1 is *stable* under its parameters and
found it is (ρ 0.93–1.00 across Δ, cutoffs, edge noise). Stability is not the question that matters. The
question is whether the number A1 ranks on is the quantity we say it is. Every hypothesis below has a
prediction that can fail, and the grid is what makes them falsifiable.

Read the grid as: **H1–H4 are properties A1 would have if it measured "influence" well. E1–E3 are ways it
could be measuring something else.** A confirmation of an E is a finding about the metric, not a bug in it.

---

## Section 0 — Probes already run (exploratory, not counted as tests)

These are what suggested the grid; they are reported so the hypotheses are not back-fitted to them.
None of them had a written prediction in advance, so none of them counts as a confirmation.

| probe | number | how I would misread it |
|---|---|---|
| score vs per-paper average | ρ 0.937 | "A1 is just volume." The top-10 by per-paper average (Eric Brill, Kristina Klinkner, Alan Halverson, Martin Szummer, Li-wei He, Daniel Ramage, Steffen Rendle …) shares **one name** with the top-10 by score. Both readings are available from the same 0.937. |
| score share of total | top 10 authors = 13.4 %, top 50 = 36.1 %, top 100 = 49.5 % | a 1,430-author ranking where 100 people hold half the mass. Flat enough that a small score change does not move rank much — which is *why* ρ stays high under perturbation. High stability may be a property of the flatness, not of the signal. |
| self-citations | 17.9 % of edges; median author-level self-share 0.25 | dropped later in H3. |
| in-window citations per paper | 36.9 % of cited papers have **exactly one** | a third of the evidence base is a count of one. |
| half-split (2006–09 vs 2010–14) | ρ 0.49, top-100 overlap 52 of 100 | the strongest signal in the probes. If an author's standing is a real property, two disjoint halves of the same field should agree far better than this. |
| earliest-citation lag | mean lag 1.86 yr at top, 1.84 yr overall; ρ(mean lag, score) 0.13 | no "fast risers" story survives. |

---

## Section 1 — Hypotheses

### H1. The score is flat, and flatness is what the stability results were measuring
**Claim.** A1's score distribution is close to uniform over its 1,430 authors, in the sense that no small
set of authors dominates; the high ρ values reported for parameter changes come from this flatness rather
than from a sharply defined property.

**Prediction.** Top-10 % of authors (143) hold between 45 % and 60 % of total score; the ratio of the
90th to the 50th percentile score is under 4×; dropping the top 20 authors changes no other author's rank
position (they only shift up).

**Fails if.** The distribution is heavy-tailed (top 10 % > 70 % of mass) — then the stability results *are*
about a sharp ranking and this explanation collapses.

**Why it matters for the deck.** The sensitivity slide currently sells stability as evidence of a sound
metric. If H1 holds, that slide says something weaker: *A1 agrees with itself because its scores are
compressed, not because its rankings are well determined.*

---

### H2. An author's standing is mostly *which birth years they happen to occupy*
**Claim.** The half-split disagreement (ρ 0.49) is not noise. Within the fixed window 2006–2014, citations
per paper fall steeply with birth year — 12.0 (2006) to 5.7 (2014) in the whole graph — because an earlier
paper has had longer to be cited by the fixed cutoff. A1's window [y, y+3] equalises this *per paper*, but
it cannot equalise *who* the author is in the field across the two halves. The score therefore largely
measures cohort position.

**Prediction.** (a) Repeating the half-split on a cohort-matched sample (author's papers resampled so both
halves have the same birth-year mix) raises ρ from ~0.49 to **≥ 0.70**. (b) Among authors whose entire
career in-window lies in one half, the cross-half ρ is undefined but their mean score differs in the
direction of birth year: mean score of 2006–07 authors exceeds that of 2012–14 authors by **≥ 1.5×**.

**Fails if.** Cohort matching leaves ρ near 0.49 — then the instability is about the citation process, not
about the cohort, and H2 is wrong in the way that matters.

**This is the one I would spend the next run on.** It separates "the metric is noisy" from "the metric ranks
age", and those two need completely different fixes.

---

### H3. Self-citation is not doing the work
**Claim.** A1 includes self-citations (17.9 % of edges, median 25 % of an author's cited evidence). The
"safe" fix — strip them — barely changes the ranking.

**Prediction.** ρ(base, no-self-citations) **≥ 0.95**; top-100 overlap **≥ 90**; ≥ 500 of 1,430 authors
unchanged in score.

*Exploratory value already observed: ρ 0.963, top-100 91. That matches, but it was run before this
document, so it is listed here as a prediction that will be re-run with the fixed grid, not as a result.*

**Why it matters.** Someone will ask "isn't this just people citing themselves?" The answer is a number, and
we should have it ready. If H3 fails (ρ < 0.90), self-citation becomes a headline finding instead.

---

### E1. A large share of the score rests on single citations
**Claim.** Because 36.9 % of cited in-window papers have exactly one in-window citation, a meaningful part of
each author's score is a sum of fractions from papers with one observation each. The ranking is therefore
sensitive to a single missing edge for a big subset of authors.

**Prediction.** For ≥ 40 % of authors, **≥ 50 %** of their score comes from papers with ≤ 2 in-window
citations. Restricting to papers with ≥ 3 citations keeps ≥ 60 % of the 1,430 authors and yields ρ **≤ 0.75**
against the base — i.e. the thin-evidence half of the score is not redundant with the thick half.

**Fails if.** ρ(base, thick-only) ≥ 0.90 on the shared authors — then thin evidence is not carrying
independent weight and this concern is cosmetic.

---

### E2. Venue priors leak into the score through the denominator
**Claim.** `share(p)` divides by a *single* field-wide denominator per year, so a paper published at a venue
whose papers are cited more per year is rewarded for its venue, independent of the paper's own quality.
ρ(tois_frac, score) = 0.23 suggests TOIS-heavy authors do better, but 0.23 could be quality.

**Prediction.** Conditioning on an author's **primary** venue, within-venue score distributions overlap
heavily (a CIKM-primary author appears in the top 100 for every venue group), and the *between* venue
groups' median scores differ by **< 20 %**. Sweeping the venue mix of a synthetic author (same per-paper
citations, papers re-labelled across venues) changes their score by < 10 %.

**Fails if.** Venue group medians differ by ≥ 2× — then A1 partly ranks "published in TOIS", and the
field-share normalisation it was built to fix is not actually normalising.

---

### E3. The score is not the sum of its papers' standalone quality
**Claim.** The per-paper → per-author aggregation is where A1 quietly makes a choice. `Σ share/n` rewards an
author whose *papers* cross domains (smaller `n`, bigger per-person credit) over one whose papers are in
large teams, at equal paper quality. That is an authorship-volume effect dressed as a quality signal.

**Prediction.** Holding `Σ share` fixed at ±10 %, authors with smaller mean `n_papers`-team-size-slot
(mean `n` across their papers) rank higher; ρ(mean `n_authors`, score) is **≤ −0.3**. The same ranking
computed with **full** credit per paper (`Σ share`, no `/n`) disagrees at ρ **≤ 0.7**.

**Fails if.** ρ(full-credit, A1) ≥ 0.9 — then `/n` is a rounding detail and the aggregation is not a lever.

---

## Section 2 — What each outcome would mean for the project

| If this holds | Then in the deck / report |
|---|---|
| H1 | the "stability" slide must be re-captioned as a flatness result, not a robustness result |
| H2 | A1 is a cohort-position metric in a fixed window; the honest fix is evaluating against an external label (awards), not another internal re-weighting |
| H3 | the obvious objection is answered with a number; one slide line, no redesign |
| E1 | the score's effective sample size is far below its paper count; report it, don't hide it |
| E2 | the field-share denominator needs a venue-level denominator; this is the one change that is a genuine improvement, not a re-weighting |
| E3 | `/n` is a policy choice to state explicitly, and A2/A3's disagreement with A1 must be read against it |

The through-line: **A1 stops looking like "the field-normalised citation ranking" and starts looking like a
metric with four named properties, three of which a reader must be told.** That is the version of the
method-slide that survives Soumen sir's first question.

---

## Section 3 — Pre-registered grid (write the number down before running)

| # | Test | Threshold for "holds" | Threshold for "fails" |
|---|---|---|---|
| H1 | top-10 % score share | 0.45–0.60 | > 0.70 |
| H2 | ρ half-split, cohort-matched | ≥ 0.70 | < 0.60 |
| H2 | mean score, 2006–07 vs 2012–14 authors | ≥ 1.5× | ≤ 1.1× |
| H3 | ρ base vs no-self | ≥ 0.95 | < 0.90 |
| E1 | share of authors with ≥ 50 % thin score | ≥ 0.40 | < 0.20 |
| E1 | ρ base vs thick-only | ≤ 0.75 | ≥ 0.90 |
| E2 | venue-group median score spread | < 1.2× | ≥ 2× |
| E3 | ρ(mean team size, score) | ≤ −0.30 | > −0.10 |

Anything landing between "holds" and "fails" is reported as an open question with the number, not resolved
by prose.

---

## Section 4 — Cost

| test | run time | data already there? |
|---|---|---|
| H1 | seconds | yes |
| H2 | ~5 min (needs a cohort-matched resampler over 5,317 papers) | yes |
| H3 | minutes | yes |
| E1 | seconds | yes |
| E2 | ~10 min (needs a synthetic re-labelling sweep) | yes |
| E3 | seconds | yes |

**No new downloads.** Every test runs on `C:/ranking_data/ir/works.parquet` and
`C:/ranking_data/work/ir_edges.parquet` as they stand.

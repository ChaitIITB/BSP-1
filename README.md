# CS6101 — Ranking Researchers by Citation Value

Comparing five approaches to ranking researchers in a field by citation value,
evaluated against one future-citation outcome, plus a set of alternative citation
metrics (M1–M4, B1–B2, the citation deflator, and a literature review of what else
the field uses).

Course project, IIT Bombay, CS6101 (autumn 2026).

## What the project asks

Given a set of papers in a field, their citation graph, and each paper's authors,
produce a ranking of the authors. Every approach is scored the same way: does its
ordering agree with the citations those authors' existing papers receive in the
*next* four years?

**Outcome** (`outcome()` in `scripts/approaches.py`): for each author, the citations
received in 2018–2022 by their papers published up to 2017, split 1/n across
co-authors. This is the single yardstick all approaches are measured against.

**Evaluation** (`evaluate()`): Spearman correlation between the approach's ranking
and the outcome ranking (higher is better), plus an age-bias number: the Spearman
correlation of the score with the author's average birth year of their 2006–2014
papers. **A negative age-bias value means older authors score higher.**

## Approaches

| # | Approach | Where |
| --- | --- | --- |
| 1 | Field share: an author's share of the citations their papers' cohort collects, within a 3-year window | `scripts/approach1.py`, `approaches.a1` |
| 2 | LLM writes the ranking as SQL | `scripts/a2_llm.py`, `sql/` |
| 3 | LLM proposes ranking rules, iterated for four rounds | `approaches.a3`, `rank_A3r*.csv` |
| 4 | GenRec-style LoRA fine-tune of Qwen2.5-1.5B, trained on Kaggle GPU | `scripts/kaggle_genrec_rank.py`, `kaggle/` |
| — | Metrics M1–M4, B1, B2 (mean-normalised share, h-index style, share of top-10% papers, distinct-paper share, …) | `approaches.py`, `scripts/metrics_run.py` |
| — | Citation deflator (correcting for citation inflation) | `approaches.py` (`deflator`, `d1`, `d2`, `b1p`), `scripts/deflator_run.py` |

## Results

| Dataset | Approach | Spearman vs outcome | Age bias |
| --- | --- | --- | --- |
| OpenAlex IR subset | A1 field share | 0.708 | −0.178 |
| Semantic Scholar IR subset | A1 field share | 0.502 | −0.002 |
| OpenAlex IR subset | D1 (deflated share) | 0.694 | −0.217 |
| Semantic Scholar IR subset | D1 (deflated share) | 0.499 | −0.008 |

Full tables and verdicts:

- `results/metrics/RESULTS.md` — M1–M4, B1, B2 against pre-registered hypotheses
- `results/metrics/RESULTS_DEFLATOR.md` — the deflator strand
- `results/ir_sensitivity/` — noise floor (20 runs, 20% edge drops: ρ moves ≤ 0.014) and cutoff sweeps

Short version of the findings:

- Field share (A1) is a strong predictor of future citations, and the whole
  deflator strand **failed to fix age bias** while costing 0.014 ρ — a negative result,
  documented.
- M1 rediscovered MNCS (Waltman & van Eck, 2019) and reproduced its documented failure
  mode: small-n instability and one-hit authors.
- The GenRec fine-tune beats random but does not beat a simple baseline.

## Pre-registration

Hypotheses were written down *before* each metric was run, with a noise band of 0.03
ρ from the measured noise floor:

- `METRIC_PLAN.md` — H1–H4
- `METRIC_PLAN_DEFLATOR.md` — H5–H8 and the deflator amendment
- `results/ir_sensitivity/metric_hypotheses.md`

## Literature review

- `METRIC_LITERATURE_REVIEW.md` — 12 metric families (W1–W12) ranked, with bibliography
- `LITERATURE_REVIEW_METHOD.md` — the review procedure (PRISMA counts, TARCiS citation
  searching), the term table, and the search queries
- `literature_search_step1.json` — the novelty check on the two remaining candidate
  metrics, with every query logged (database, date, hit count)

## Data

The data is **not** in this repository (it is ~5 GB of Parquet). It lives outside it,
at `C:/ranking_data`:

```
C:/ranking_data/
  work/          ir_*, irs2_*, cs_*  (authors, edges, citing authors)
  ir/works.parquet          OpenAlex IR subset (~1.4k authors)
  ir_s2/s2_papers.parquet   Semantic Scholar copy of the same set
  data/meta.parquet         arXiv metadata, 3.2M titles
```

Rebuild it from source with `scripts/fetch_openalex.py`, `scripts/fetch_s2_for_set.py`,
`scripts/build_ir.py`, `scripts/build_ir_s2.py`, `scripts/build_cs_base.py`.
`raw/README.txt` records the source.

If you re-create the data somewhere else, edit `DATA` and `WORK` at the top of
`scripts/rank_lib.py`.

## Reproducing

```bash
pip install duckdb pyarrow pandas numpy scipy
```

`RANK_FIELD=ir|irs2|cs` selects which dataset the scripts read (default `cs`).
Run the scripts from the data directory, so relative paths resolve:

```bash
cd C:/ranking_data
python -X utf8 path/to/ranking_project/scripts/approach1.py
python -X utf8 .../scripts/metrics_run.py
python -X utf8 .../scripts/deflator_run.py
python -X utf8 .../scripts/sensitivity.py
```

The LLM approaches need three environment variables (never files):

```
LLM_BASE_URL   LLM_API_KEY   LLM_MODEL
```

The OpenAlex and Semantic Scholar fetchers read `OPENALEX_KEY` and `S2_KEY` from the
environment. The Kaggle fine-tune needs a Kaggle token in `~/.kaggle/`; see
`kaggle/kernel-metadata.json`.

## Decks and report

- `progress_update_presentation.html` — the main deck (24 slides), standalone: open it in any browser
- `lora_slides.html` — the LoRA / training-script deck kept separate from the main one
- `report.html` — the written report

## Licence

MIT — see `LICENSE`.

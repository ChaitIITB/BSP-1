# Sensitivity of Approach 1 to its parameters: hypotheses (written 2026-10-27, BEFORE any run)

Data: OpenAlex IR graph (14,462 papers, 54,351 edges). Approach 1 as in `scripts/approaches.py` (`a1`).
No outcome-based (future-citation) metric is used. All comparisons are between rankings or properties of the data.
Baseline setting: delta = 3, cutoff = 2014, birth_min = 2006, min_papers = 3.

Measures: Spearman between rankings on the authors both have; top-100 overlap; fraction of tied scores; age bias (Spearman of score with mean birth year).

## Hypotheses (with predictions that can fail)

H1 (window length, delta in {1,2,3,5,8}). Short windows are noisy: fewer citations per paper, more ties and zero scores.
  Predictions: tied fraction falls as delta grows; Spearman(delta=3, delta=5) >= 0.90; Spearman(delta=3, delta=1) <= 0.85.

H2 (how fast citations arrive, the Relay-Linking age gap). IR citations arrive quickly, so delta = 3 is a sensible default.
  Rule fixed in advance: delta_half = smallest gap (years) by which half of a paper's in-set citations (papers born 2006-2014, counted up to 2022) have arrived.
  Prediction: delta_half in {2, 3, 4}; 80% of citations arrive within 7 years.

H3 (field-specific delta). Journals (TOIS, Information Retrieval) are cited more slowly than conferences (SIGIR, CIKM, WSDM).
  Prediction: median age gap of cited journal papers exceeds that of cited conference papers by at least 0.5 year.

H4 (cutoff, in {2010, 2012, 2014, 2016}). Moving the cutoff mostly adds or removes recent papers; long-career authors keep their place.
  Predictions: Spearman(cutoff 2014, cutoff 2012) >= 0.85 on common authors; top-100 overlap with cutoff 2014 decreases as the cutoff moves further away (2016 and 2012 above 2010).

H5 (noise floor). Keeping a random 80% of the edges changes the ranking little.
  Predictions (20 repeats): median Spearman with the full ranking >= 0.95; median top-100 overlap >= 80.
  Use: differences between settings smaller than this noise are not evidence of a real difference.

H6 (age bias). Dividing by the field's window total absorbs differences in field size across years, so age bias stays similar across delta.
  Prediction: age bias stays within +/- 0.10 of the baseline (-0.18) for delta in {2,3,5,8}.

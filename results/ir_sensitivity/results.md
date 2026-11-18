# Results (run after hypotheses.md was written; script: scripts/sensitivity.py, CSVs in this folder)

| # | Prediction | Result | Verdict |
|---|---|---|---|
| H1 | ties fall as delta grows | 40.5%, 27.1%, 22.4%, 18.7%, 16.9% for delta 1,2,3,5,8 | held |
| H1 | Spearman(d3,d5) >= 0.90 | 0.984 | held |
| H1 | Spearman(d3,d1) <= 0.85 | 0.928 | **failed**: delta=1 is noisier but still agrees strongly |
| H2 | delta_half in {2,3,4} | 3 | held, with a caveat below |
| H2 | 80% of citations within 7 years | 80% by gap 6 | held, same caveat |
| H3 | journal median gap >= 0.5 year above conference | medians 4 vs 3 (whole years); means 4.06 vs 3.73 (+0.33) | **inconclusive**: median differs by 1 year but resolution is whole years and the mean differs by less than 0.5 |
| H4 | Spearman(cutoff 2014, 2012) >= 0.85 | 0.974 | held |
| H4 | top-100 overlap with 2014: 2016 and 2012 above 2010 | 92, 90, 85 | held |
| H5 | 80% edges: median Spearman >= 0.95 | 0.989 (range 0.987-0.991) | held |
| H5 | median top-100 overlap >= 80 | 95 (range 92-98) | held |
| H6 | age bias within +/-0.10 of -0.178 for delta 2,3,5,8 | -0.189, -0.178, -0.163, -0.166 | held |

Caveats
- H2 uses only gaps <= 8 years, so that every birth cohort (2006-2014) is observed equally. This cuts off the slow tail. For the 2006-2010 cohort with no cap, the median gap is 5 years and 80% arrive by 9 years. So delta_half = 3 is the answer under the 8-year cap, not a cap-free fact.
- Years only (no months), so medians move in whole years.
- Not in the hypotheses: age bias moves more with the cutoff (-0.24 at 2012, -0.13 at 2016) than with delta.
- Noise floor vs setting effects: random loss of 20% of edges gives Spearman about 0.989 and top-100 overlap 92-98. Delta 2 (0.982, 94) and delta 5 (0.984, 91) are about at the noise level; delta 1 (0.928, 86) and delta 8 (0.971, 86) are clearly below it.

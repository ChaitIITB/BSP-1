"""Metric comparison: A1 plus the productivity-normalized family. Run from C:/ranking_data:
   RANK_FIELD=ir python <repo>/scripts/metrics_run.py"""
import os
import pandas as pd
from scipy.stats import spearmanr
from rank_lib import connect, WORK
import approaches as A

if __name__ == '__main__':
    c = connect()
    A.setup(c)
    fut = A.outcome(c)
    K = [('A1 total share (reference)', A.a1), ('M1 per-paper share (normalised)', A.m1),
         ('M2 median paper share', A.m2), ('M3 top-3 mean share', A.m3),
         ('M4 shrunk per-paper share', A.m4), ('B1 per-paper citations', A.b1),
         ('B2 h-like (papers with 3+ cites)', A.b2)]
    R, rows = {}, []
    for nm, fn in K:
        key = nm.split()[0]
        R[key] = fn(c)
        rows.append(A.evaluate(nm, R[key], fut, c))
    ev = pd.DataFrame(rows)
    print(ev.to_string(index=False))
    ev.to_csv(f'{WORK}/{A.FIELD}_metric_table.csv', index=False)

    ag = []
    for k, v in R.items():
        if k == 'A1':
            continue
        d = A.agree(R['A1'], v)
        d['metric'] = k
        ag.append(d)
        print('\nA1 vs', k, d)
    pd.DataFrame(ag)[['metric', 'n', 'spearman', 'kendall', 'top100_overlap']].to_csv(
        f'{WORK}/{A.FIELD}_agree_matrix.csv', index=False)

    print('\nage bias across birth year (M1 vs A1): correlation of score with n_papers and with year')
    for k in ('A1', 'M1', 'M4', 'B1'):
        d = R[k].merge(c.execute("select author, avg(year) as my from authors where year between "
                                 f"{A.BIRTH_MIN} and {A.CUTOFF} group by 1").df(), on='author')
        print(k, 'rho(n_papers, year)=', round(spearmanr(d.n_papers, d.my)[0], 3),
              ' rho(score, n_papers)=', round(spearmanr(d.score, d.n_papers)[0], 3))
    for k in ('A1', 'M1', 'M4', 'B1'):
        print('\nTop 10', k)
        print(R[k].nlargest(10, 'score').to_string(index=False))
        R[k].sort_values('score', ascending=False).to_csv(f'{WORK}/{A.FIELD}_rank_{k}.csv', index=False)

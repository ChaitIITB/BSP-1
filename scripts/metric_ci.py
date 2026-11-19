"""Bootstrap confidence intervals for (rho future, age bias, top-100 overlap with A1).

Resamples the 1,430 scored authors with replacement (paper-level resampling would not move
author scores), so the interval answers "how much of this difference is sampling noise in the
author population". 2000 draws, seed fixed so the numbers in the report are reproducible.

Run from C:/ranking_data:  RANK_FIELD=ir python <repo>/scripts/metric_ci.py
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from rank_lib import connect, WORK
import approaches as A

B = 2000
SEED = 20261119


def stats(score, fut, my, a1_rank_ids, top=100):
    s = pd.Series(score)
    return (spearmanr(s, fut)[0], spearmanr(s, my)[0],
            len(set(s.nlargest(top).index) & a1_rank_ids))


if __name__ == '__main__':
    c = connect()
    A.setup(c)
    fut = A.outcome(c)
    age = c.execute(f"select author, avg(year) as my from authors0 "
                    f"where year between {A.BIRTH_MIN} and {A.CUTOFF} group by 1").df()

    M = {'A1': A.a1, 'M1': A.m1, 'M2': A.m2, 'M3': A.m3, 'M4': A.m4, 'B1': A.b1, 'B2': A.b2}
    R = {k: f(c) for k, f in M.items()}
    base = R['A1'].set_index('author').score

    rows = []
    rng = np.random.default_rng(SEED)
    idx = [None] * B
    for k, df in R.items():
        d = df.set_index('author').join(fut.set_index('author'), how='left').join(age.set_index('author'), how='left')
        d['future'] = d.future.fillna(0)
        d = d.dropna(subset=['my'])
        rows.append(dict(metric=k, n=len(d), **dict(zip(
            ('rho_future', 'age_bias', 'top100_overlap_A1'),
            stats(d.score, d.future, d.my, set(base.nlargest(100).index))))))

    # common bootstrap resample of authors, so differences between metrics are paired
    d0 = R['A1'].set_index('author').join(age.set_index('author'), how='left').dropna(subset=['my'])
    authors = d0.index.to_numpy()
    for b in range(B):
        idx[b] = rng.choice(len(authors), len(authors), replace=True)
    boot = {k: [] for k in R}
    for k, df in R.items():
        d = df.set_index('author').join(fut.set_index('author'), how='left').join(age.set_index('author'), how='left')
        d['future'] = d.future.fillna(0)
        d = d.reindex(authors).dropna(subset=['my'])
        sc, fu, myv = d.score.to_numpy(), d.future.to_numpy(), d.my.to_numpy()
        for b in range(B):
            i = idx[b]
            boot[k].append(stats(sc[i], fu[i], myv[i], set(authors[np.argsort(-sc[i])[:100]])))

    out = []
    for r in rows:
        arr = np.array(boot[r['metric']], dtype=float)
        for j, nm in enumerate(('rho_future', 'age_bias', 'top100_overlap_A1')):
            lo, hi = np.nanpercentile(arr[:, j], [2.5, 97.5])
            out.append(dict(metric=r['metric'], stat=nm, point=round(r[nm], 4),
                            ci_lo=round(float(lo), 4), ci_hi=round(float(hi), 4)))
        # paired difference vs A1 on the same resamples
        if r['metric'] != 'A1':
            a = np.array(boot['A1'], dtype=float)[:, :2]
            m = np.array(boot[r['metric']], dtype=float)[:, :2]
            dif = m - a
            for j, (nm, base_nm) in enumerate((('d_rho_future', 'rho_future'), ('d_age_bias', 'age_bias'))):
                lo, hi = np.nanpercentile(dif[:, j], [2.5, 97.5])
                out.append(dict(metric=r['metric'], stat=nm, point=round(r[base_nm] - [x for x in rows if x['metric'] == 'A1'][0][base_nm], 4),
                                ci_lo=round(float(lo), 4), ci_hi=round(float(hi), 4)))

    res = pd.DataFrame(out)
    print(res.to_string(index=False))
    res.to_csv(f'{WORK}/{A.FIELD}_metric_ci.csv', index=False)

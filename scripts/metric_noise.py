"""Noise floor for each metric: drop 20% of edges, recompute, 20 runs; spread of rho vs the full-data score."""
import os
import numpy as np
import pandas as pd
from rank_lib import connect, WORK
import approaches as A

if __name__ == '__main__':
    c = connect()
    A.setup(c)
    M = {'A1': A.a1, 'M1': A.m1, 'M2': A.m2, 'M3': A.m3, 'M4': A.m4, 'B1': A.b1, 'B2': A.b2}
    full = {k: f(c) for k, f in M.items()}
    rng = np.random.default_rng(0)
    n = c.execute("select count(*) from edges").fetchone()[0]
    rows = []
    for run in range(20):
        keep = rng.random(n) > 0.2
        c.execute("drop table if exists e_full"); c.execute("create table e_full as select * from edges")
        ids = c.execute("select rowid from e_full").fetchdf().rowid.values
        kept = pd.DataFrame({'rowid': ids[keep]})
        c.register('kept', kept)
        c.execute("create or replace table edges as select e.* from e_full e join kept k on k.rowid = e.rowid")
        c.execute("drop table if exists e_full")
        for k, f in M.items():
            d = full[k].merge(f(c), on='author', suffixes=('_f', '_s'))
            rows.append(dict(run=run, metric=k, common=len(d),
                             spearman=round(float(np.corrcoef(d.score_f.rank(), d.score_s.rank())[0, 1]), 3),
                             top100_overlap=len(set(d.nlargest(100, 'score_f').author) &
                                                set(d.nlargest(100, 'score_s').author))))
        for t in ('edges', 'authors', 'cau'):
            c.execute(f"drop table if exists {t}")
        A.setup(c)
        print('run', run, flush=True)
    df = pd.DataFrame(rows)
    s = df.groupby('metric').agg(rho_min=('spearman', 'min'), rho_med=('spearman', 'median'),
                                 ov_min=('top100_overlap', 'min'), ov_med=('top100_overlap', 'median')).reset_index()
    print(s.to_string(index=False))
    df.to_csv(f'{WORK}/{A.FIELD}_metric_noise.csv', index=False)
    s.to_csv(f'{WORK}/{A.FIELD}_metric_noise_summary.csv', index=False)

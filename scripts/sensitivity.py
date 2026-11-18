"""Sensitivity of Approach 1 (see results/ir_sensitivity/hypotheses.md, written before this was run).
Run from C:/ranking_data:  RANK_FIELD=ir python <repo>/scripts/sensitivity.py"""
import os, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import approaches as A
from rank_lib import connect, WORK
OUT = os.path.join(A.REPO, 'results', 'ir_sensitivity'); os.makedirs(OUT, exist_ok=True)
c = connect(); A.setup(c)
c.execute("create table edges_full as select * from edges")

def age(cutoff):
    return c.execute(f"select author, avg(year) as my from authors where year between {A.BIRTH_MIN} and {cutoff} group by 1").df()

def stats(df, cutoff):
    d = df.merge(age(cutoff), on='author')
    return dict(n=len(df), tie_frac=round(1 - df.score.nunique() / len(df), 3), age_bias=round(spearmanr(d.score, d.my)[0], 3))

def compare(a, b):
    m = a.merge(b, on='author', suffixes=('_a', '_b'))
    top = lambda df, col: set(df.nlargest(100, col).author)
    return dict(common=len(m), spearman=round(spearmanr(m.score_a, m.score_b)[0], 3), top100_overlap=len(top(m, 'score_a') & top(m, 'score_b')))

R = {}
# ---- E1: delta sweep
rows = []
for d in (1, 2, 3, 5, 8):
    R[d] = A.a1(c, delta=d)
for d in (1, 2, 3, 5, 8):
    rows.append(dict(delta=d, **stats(R[d], A.CUTOFF), **{'vs_delta3_' + k: v for k, v in compare(R[d], R[3]).items() if k != 'common'}))
e1 = pd.DataFrame(rows); e1.to_csv(f'{OUT}/delta_sweep.csv', index=False); print('E1 delta sweep\n', e1.to_string(index=False))

# ---- E2: age-gap of citations (cited papers born 2006-2014, gaps observable for all cohorts: <= 8 years)
w = c.execute("select id, venue from read_parquet('ir/works.parquet')").df()
c.register('wv', w)
g = c.execute("""select e.y_citing - e.y_cited as gap, wv.venue from edges_full e join wv on wv.id = e.cited
                 where e.y_cited between 2006 and 2014""").df()
def cdf(x, maxgap=8):
    x = x[x.gap <= maxgap]; p = x.gap.value_counts().reindex(range(maxgap + 1), fill_value=0).sort_index().cumsum() / len(x)
    return p
p_all = cdf(g)
dh = int(p_all[p_all >= 0.5].index[0]); d80 = int(p_all[p_all >= 0.8].index[0])
print('\nE2 cumulative share of in-set citations by gap (<=8y basis):\n', p_all.round(3).to_dict())
print('delta_half =', dh, ' gap for 80% =', d80)
old = g[(g.gap >= 0)]
c.register('g_dummy', g)
g_old = c.execute("""select e.y_citing - e.y_cited as gap from edges_full e where e.y_cited between 2006 and 2010""").df()
full = g_old.gap.value_counts().sort_index().cumsum() / len(g_old)
print('cohort 2006-2010, all gaps: median gap', int(full[full >= .5].index[0]), ' 80% by', int(full[full >= .8].index[0]))
jr = {'TOIS', 'IRJ'}
g['kind'] = np.where(g.venue.isin(jr), 'journal', 'conference')
vt = []
for k, x in g.groupby('kind'):
    p = cdf(x); vt.append(dict(kind=k, citations=len(x[x.gap <= 8]), median_gap=int(p[p >= .5].index[0]), gap80=int(p[p >= .8].index[0]), mean_gap=round(x[x.gap <= 8].gap.mean(), 2)))
for v, x in g.groupby('venue'):
    p = cdf(x); vt.append(dict(kind=v, citations=len(x[x.gap <= 8]), median_gap=int(p[p >= .5].index[0]), gap80=int(p[p >= .8].index[0]), mean_gap=round(x[x.gap <= 8].gap.mean(), 2)))
e2 = pd.DataFrame(vt); e2.to_csv(f'{OUT}/age_gap_by_venue.csv', index=False); print(e2.to_string(index=False))
p_all.round(4).to_csv(f'{OUT}/age_gap_cdf.csv', header=['cum_share'])

# ---- E3: cutoff sweep
res = {y: A.a1(c, cutoff=y) for y in (2010, 2012, 2014, 2016)}
rows = [dict(cutoff=y, **stats(res[y], y), **{'vs_2014_' + k: v for k, v in compare(res[y], res[2014]).items()}) for y in res]
e3 = pd.DataFrame(rows); e3.to_csv(f'{OUT}/cutoff_sweep.csv', index=False); print('\nE3 cutoff sweep\n', e3.to_string(index=False))

# ---- E4: noise floor, keep 80% of edges, 20 repeats
base = R[3]; rows = []
for i in range(20):
    c.execute(f"create or replace table edges as select * from edges_full using sample 80 percent (bernoulli, {100 + i})")
    cm = compare(A.a1(c), base); rows.append(cm)
c.execute("create or replace table edges as select * from edges_full")
e4 = pd.DataFrame(rows); e4.to_csv(f'{OUT}/noise_floor.csv', index=False)
print('\nE4 noise floor (20 repeats, 80 percent of edges): spearman median %.3f min %.3f; top100 overlap median %d min %d' % (e4.spearman.median(), e4.spearman.min(), e4.top100_overlap.median(), e4.top100_overlap.min()))
json.dump(dict(delta_half=dh, gap80=d80), open(f'{OUT}/summary.json', 'w'))

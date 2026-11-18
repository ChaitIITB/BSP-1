"""Citation deflator run (METRIC_PLAN_DEFLATOR.md steps 3-6).

Compares A1, M1, B1 against D1, D2, B1' on the same outcome. Run from C:/ranking_data:
    RANK_FIELD=ir python -X utf8 <repo>/scripts/deflator_run.py

Checks run before any result is reported:
  (a) R(t) is inspected (written to ir_Rt_*.csv by the deflator_* scripts)
  (b) the share of in-window edges with no usable R(t) is small
  (c) with D(t) = 1 everywhere, the deflated pipeline reproduces A1 exactly (rho 1.000000)
"""
import os
import pandas as pd
from scipy.stats import spearmanr
from rank_lib import connect, WORK
import approaches as A

OUT = os.path.join(A.REPO, 'results', 'metrics')


def names(c):
    """Author-id -> name for whichever graph FIELD points at. OpenAlex uses `ir/works.parquet`
    (author_ids + author_names are parallel lists); the Semantic Scholar pull keeps its own
    author_ids/author_names in s2_papers.parquet, so one helper does not fit both."""
    src = ("'C:/ranking_data/ir/works.parquet'"
           if A.FIELD != 'irs2' else "'C:/ranking_data/ir_s2/s2_papers.parquet'")
    return c.execute(f"""select author, any_value(name) as name from (
        select unnest(author_ids) as author, unnest(author_names) as name
        from read_parquet({src})) where author is not null group by 1""").df()


if __name__ == '__main__':
    c = connect('4G')
    A.setup(c)
    fut = A.outcome(c)
    R_t = A.deflator(c)
    print('R(t) = references per pool paper, D(t) = R(2021)/R(t):')
    print(R_t.assign(D=R_t.D.round(4), R=R_t.R.round(2)).to_string(index=False))

    A.a1(c)
    miss = c.execute(f"""select count(*) total,
        count(*) filter (where d.D is null) dropped
      from edges e left join deflator d on d.year = e.y_citing
      where e.y_citing <= e.y_cited + {A.DELTA} and e.y_cited between {A.BIRTH_MIN} and {A.CUTOFF}""").df()
    print('\nin-window edges:', miss.to_string(index=False))

    # (c) identity test: D = 1 must reproduce A1 exactly
    A.d1(c)
    ref = c.execute("select D from deflator where year = ?", [A.T0]).fetchone()[0]
    c.execute("update deflator set D = 1.0")
    a1 = A.a1(c)
    d1_flat = A.d1(c)
    m = a1.merge(d1_flat, on='author', suffixes=('_a1', '_d1'))
    rel = ((m.score_a1 - m.score_d1).abs() / m.score_a1.abs().clip(lower=1e-12))
    rho = spearmanr(m.score_a1, m.score_d1)[0]
    print('\nIDENTITY TEST  D(t)=1 vs A1: n=%d  rho=%.8f  max rel err=%.2e  %s'
          % (len(m), rho, rel.max(), 'PASS' if rho > 1 - 1e-9 and rel.max() < 1e-9 else 'FAIL'))
    c.execute("update deflator set D = ? / R", [ref])

    K = [('A1 total share (reference)', A.a1), ('M1 per-paper share', A.m1),
         ('B1 per-paper citations', A.b1), ('D1 deflated total share', A.d1),
         ('D2 deflated per-paper share', A.d2), ('B1p deflated per-paper cites', A.b1p)]
    R, rows = {}, []
    for nm, fn in K:
        key = nm.split()[0]
        R[key] = fn(c)
        rows.append(A.evaluate(nm, R[key], fut, c))
    ev = pd.DataFrame(rows)
    print('\n' + ev.to_string(index=False))
    ev.to_csv(os.path.join(OUT, f'{A.FIELD}_deflator_table.csv'), index=False)

    ag = []
    for k, v in R.items():
        if k == 'A1':
            continue
        d = A.agree(R['A1'], v)
        d['metric'] = k
        ag.append(d)
    AG = pd.DataFrame(ag)[['metric', 'n', 'spearman', 'kendall', 'top100_overlap']]
    print('\nagreement with A1:')
    print(AG.to_string(index=False))
    AG.to_csv(os.path.join(OUT, f'{A.FIELD}_deflator_agree.csv'), index=False)

    age = c.execute("select author, avg(year) as my from authors0 where year between "
                    f"{A.BIRTH_MIN} and {A.CUTOFF} group by 1").df()
    print('\nwho moves: mean birth year of top-10 / top-100 by metric (all = %.2f)' % age.my.mean())
    for k in ('A1', 'M1', 'D1', 'D2', 'B1p'):
        d = R[k].merge(age, on='author', how='left')
        print('  %-4s top10 %6.2f  top100 %6.2f' % (k, d.nlargest(10, 'score').my.mean(),
                                                    d.nlargest(100, 'score').my.mean()))

    a = R['A1'].copy(); a['rk_a1'] = a.score.rank(ascending=False).astype(int)
    d = R['D1'].copy(); d['rk_d1'] = d.score.rank(ascending=False).astype(int)
    j = a.merge(d, on='author', how='outer', suffixes=('_a1', '_d1')).merge(names(c), on='author', how='left')
    j['move'] = j.rk_a1 - j.rk_d1
    print('\ntop 12 by D1, with their A1 rank:')
    print(j.nsmallest(12, 'rk_d1')[['name', 'rk_a1', 'rk_d1', 'move', 'n_papers_d1', 'raw_cites_d1']]
          .to_string(index=False))
    print('\nbiggest fallers out of A1 top 100:')
    print(j[j.rk_a1 <= 100].nsmallest(8, 'move')[['name', 'rk_a1', 'rk_d1', 'move']].to_string(index=False))
    j.sort_values('rk_d1').to_csv(os.path.join(OUT, f'{A.FIELD}_deflator_moves.csv'), index=False)

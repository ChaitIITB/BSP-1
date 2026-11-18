"""Sensitivity check: does the choice of R(t) definition change the answer?

The plan picks outside-only references, but the curve is smooth and mildly drifting, so this script
recomputes R(t) three ways and reports the max divergence. Used to justify the definition choice with
numbers rather than assertion. Run from C:/ranking_data:
  python -X utf8 <repo>/scripts/deflator_Rt_variants.py
"""
import os
import pandas as pd
from rank_lib import connect

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'results', 'metrics')
c = connect('4G')
c.execute("""create table pool as select id, year, refs from read_parquet('C:/ranking_data/ir/works.parquet')
  where type in ('conference-paper','article') and year is not null""")
c.execute("""create table refs as select p.year as y_citing,
    case when q.id is null then 0 else 1 end as in_pool
  from pool p, (select p2.id, unnest(p2.refs) as ref from pool p2) r
  left join pool q on q.id = r.ref where p.id = r.id""")
c.execute("""create table rt_v as select y_citing as year,
    count(*) as total,
    count(*) - sum(in_pool) as outside,
    sum(in_pool) as inpool,
    count(distinct (case when in_pool = 0 then 1 end)) as any_outside
  from refs group by 1""")
c.execute("""create table papers as select year, count(*) as n, sum(len(refs)) as refs from pool group by 1""")
R = c.execute("""select t.year, p.n as papers, t.total, t.outside, t.inpool,
    round(t.total / p.n, 2) as refs_per_paper
  from rt_v t join papers p on p.year = t.year order by 1""").df()
# t0 = first year where the crawl is complete enough; 2004 is the first year before any truncated
# venue-year drops below 35% of its median (see deflator_trust.py): 2005 is the first clean year.
T0 = 2005
R['D_total'] = (R.total / R.total[R.year == T0].iloc[0]).round(4)
R['D_outside'] = (R.outside / R.outside[R.year == T0].iloc[0]).round(4)
R['D_per_paper'] = (R.refs_per_paper / R.refs_per_paper[R.year == T0].iloc[0]).round(4)
R.to_csv(os.path.join(OUT, 'ir_Rt_variants.csv'), index=False)
print(R.to_string(index=False))
print('\ndivergence between the three definitions (|log ratio|), %d-%d:'
      % (R.year.min(), R.year.max()))
import numpy as np
for a, b in [('D_total', 'D_outside'), ('D_outside', 'D_per_paper'), ('D_total', 'D_per_paper')]:
    lr = np.abs(np.log(R[a] / R[b]))
    print('  %-12s vs %-12s  mean %.1f%%  max %.1f%%' % (a, b, lr.mean() * 100, lr.max() * 100))

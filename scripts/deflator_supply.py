"""Step 1 of METRIC_PLAN_DEFLATOR.md: build R(t), the citation supply per citing year.

R(t) = references emitted by pool papers of year t that point OUTSIDE the pool.
The in-pool alternative is written alongside so the choice in the plan can be checked, not assumed.

Run from C:/ranking_data:  python <repo>/scripts/deflator_supply.py
"""
import os
import pandas as pd
from rank_lib import connect

FIELD = os.environ.get('RANK_FIELD', 'ir')
WORK = os.environ.get('RANK_WORK', 'C:/ranking_data/work')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'results', 'metrics')


def build(c):
    c.execute(f"""create table pool as select id, year, refs from read_parquet('C:/ranking_data/ir/works.parquet')
      where type in ('conference-paper','article') and year is not null""")
    # every reference, tagged with the citing year and whether it resolves inside the pool
    c.execute("""create table refs as select p.year as y_citing, r.ref as cited,
        case when q.id is null then 0 else 1 end as in_pool
      from pool p, (select p2.id, unnest(p2.refs) as ref from pool p2) r
      left join pool q on q.id = r.ref
      where p.id = r.id""")
    return c.execute("""select y_citing as year,
          count(*) as refs_total,
          sum(in_pool) as refs_in_pool,
          count(*) - sum(in_pool) as refs_outside,
          count(distinct (case when in_pool = 0 then cited end)) as distinct_outside_cited
        from refs group by 1 order by 1""").df()


if __name__ == '__main__':
    c = connect()
    R = build(c)
    R['outside_per_paper'] = R.refs_outside / R.refs_outside.sum() * 0   # placeholder, replaced below
    papers = c.execute("select year, count(*) as papers from pool group by 1 order by 1").df()
    R = R.merge(papers, on='year', how='left')
    R['outside_per_paper'] = (R.refs_outside / R.papers).round(2)
    R['D_outside'] = (R.refs_outside / R.refs_outside.iloc[0]).round(4)   # t0 = first year
    R['grow_outside_x'] = (R.refs_outside / R.refs_outside.iloc[0]).round(2)
    R['grow_inpool_x'] = (R.refs_in_pool / R.refs_in_pool.iloc[0]).round(2)
    os.makedirs(OUT, exist_ok=True)
    R.to_csv(os.path.join(OUT, f'{FIELD}_R_t.csv'), index=False)
    print(R.to_string(index=False))
    print('\noutside references grew x%.2f from %d to %d over %d years'
          % (R.grow_outside_x.iloc[-1], R.refs_outside.iloc[0], R.refs_outside.iloc[-1], len(R)))
    print('in-pool references grew x%.2f over the same span' % R.grow_inpool_x.iloc[-1])
    print('\nwritten:', os.path.join(OUT, f'{FIELD}_R_t.csv'))

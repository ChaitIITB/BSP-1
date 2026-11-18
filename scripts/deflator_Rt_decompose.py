"""R(t) diagnostic: separate the two things that could be moving the curve.

R(t) = papers(t) x refs_per_paper(t). Growth in the first is our crawl getting bigger (way out of
proportion to IR), growth in the second is a real change in citation behaviour. The deflator is only
defensible if the ratio is dominated by the outcome being measured, so this prints the split and the
count of distinct outside works cited per year (a supply measure that does not depend on how many
papers we happen to have in the crawl).

Run from C:/ranking_data:  python -X utf8 <repo>/scripts/deflator_Rt_decompose.py
"""
import os
import pandas as pd
from rank_lib import connect

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'results', 'metrics')
c = connect('4G')
c.execute("""create table pool as select id, year, len(refs) as nref, refs from read_parquet('C:/ranking_data/ir/works.parquet')
  where type in ('conference-paper','article') and year is not null""")
c.execute("""create table rt as select y as year, count(*) as papers, sum(nref) as refs,
    sum(case when q.id is null then 1 else 0 end) as refs_out,
    count(distinct case when q.id is null then r.ref end) as distinct_out
  from (select year as y, unnest(refs) as ref, id from pool) r
  left join pool q on q.id = r.ref group by 1 order by 1""")
R = c.execute("select * from rt").df()
R['refs_per_paper'] = (R.refs / R.papers).round(2)
R['papers_x'] = (R.papers / R.papers[R.year == 2005].iloc[0]).round(2)
R['rpp_x'] = (R.refs_per_paper / R.refs_per_paper[R.year == 2005].iloc[0]).round(2)
R['outside_x'] = (R.refs_out / R.refs_out[R.year == 2005].iloc[0]).round(2)
R['distinct_out_x'] = (R.distinct_out / R.distinct_out[R.year == 2005].iloc[0]).round(2)
print(R[['year', 'papers', 'papers_x', 'refs_per_paper', 'rpp_x', 'outside_x', 'distinct_out_x']].to_string(index=False))
R.to_csv(os.path.join(OUT, 'ir_Rt_decomposed.csv'), index=False)
print('\nfrom 2005 to 2022: papers x%.1f, refs-per-paper x%.2f, outside refs x%.1f, distinct outside works cited x%.1f'
      % (R.papers_x.iloc[-1], R.rpp_x.iloc[-1], R.outside_x.iloc[-1], R.distinct_out_x.iloc[-1]))

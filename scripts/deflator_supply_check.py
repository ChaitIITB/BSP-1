"""Diagnostics for R(t) before the deflator uses it: are the dips real or artefacts of which papers
happen to be in each year of the crawl?

Run from C:/ranking_data:  python -X utf8 <repo>/scripts/deflator_supply_check.py
"""
import os
import pandas as pd
from rank_lib import connect

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'results', 'metrics')
c = connect('4GB')
c.execute("""create table pool as select id, venue, year, refs, len(refs) as nref
  from read_parquet('C:/ranking_data/ir/works.parquet')
  where type in ('conference-paper','article') and year is not null""")

print('--- refs per paper by venue and year (a year with few long-reference venues will dip) ---')
tab = c.execute("""select coarse, year, count(*) as papers, round(avg(nref),1) as mean_refs from (
    select case when venue in ('SIGIR','CIKM','WSDM','TOIS','IRJ') then venue else 'other' end as coarse,
           year, nref from pool) group by 1,2 order by 1,2""").df()
print(tab.pivot(index='year', columns='coarse', values='mean_refs').to_string())
print('\n--- papers per venue and year ---')
print(tab.pivot(index='year', columns='coarse', values='papers').fillna(0).astype(int).to_string())

print('\n--- refs per paper by publication type (journal articles cite far more than 4-page papers) ---')
print(c.execute("""select type, count(*) n, round(avg(len(refs)),1) mean_refs, min(year) y0, max(year) y1
  from read_parquet('C:/ranking_data/ir/works.parquet') where year is not null group by 1""").df().to_string(index=False))

print('\n--- per-year median refs per paper (robust to a single long-paper outlier) ---')
print(c.execute("""select year, count(*) papers, round(avg(nref),1) mean_refs, median(nref) med_refs,
    quantile_cont(nref, 0.9) p90_refs from pool group by 1 order by 1""").df().to_string(index=False))

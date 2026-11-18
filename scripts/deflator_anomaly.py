"""Anomaly check for the R(t) curve: is any year's reference count an artefact of the crawl?

2002-2003 have median 3 refs per paper while every neighbouring year has 17-20. That is not a
trend, it is a data artefact, and using it in a deflator would inflate those years by ~6x.
This script finds which source causes it. Run from C:/ranking_data:
  python -X utf8 <repo>/scripts/deflator_anomaly.py
"""
import os
import pandas as pd
from rank_lib import connect

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = connect('4G')
print('--- 2002-2003: papers per venue with refs truncated to <=4 ---')
print(c.execute("""select year, venue, count(*) papers,
    sum(case when len(refs) <= 4 then 1 else 0 end) as few_refs,
    round(100.0 * sum(case when len(refs) <= 4 then 1 else 0 end) / count(*), 1) as pct_few
  from read_parquet('C:/ranking_data/ir/works.parquet')
  where year between 2002 and 2003 and type in ('conference-paper','article')
  group by 1,2 having count(*) > 5 order by 1,3 desc""").df().to_string(index=False))

print('\n--- and the same % for every year, to see if the seam is only 2002-03 ---')
print(c.execute("""select year, count(*) papers,
    round(100.0 * sum(case when len(refs) <= 4 then 1 else 0 end) / count(*), 1) as pct_le4_refs
  from read_parquet('C:/ranking_data/ir/works.parquet')
  where type in ('conference-paper','article') and year is not null group by 1 order by 1""").df().to_string(index=False))

"""Which years' reference lists are trustworthily scraped? Needed because R(t) must not be built on
truncated reference lists.

A paper's reference list is treated as TRUNCATED if it has <= 4 refs. A finishable check is better
though: compare the number of refs with what other papers of the same year/venue have (median).
Report per year: mean refs per paper for the papers that are NOT in the truncated tail. If that
series is smooth, the tail is a scrape artefact and the year's true R(t) is better estimated from
the untruncated majority than from the full mean.

Run from C:/ranking_data:  python -X utf8 <repo>/scripts/deflator_trust.py
"""
import os
import pandas as pd
from rank_lib import connect

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'results', 'metrics')
c = connect('4G')
c.execute("""create table p as select id, venue, year, len(refs) as nref from read_parquet('C:/ranking_data/ir/works.parquet')
  where type in ('conference-paper','article') and year is not null""")
# venue-level reference-list distribution per year
c.execute("""create table q as select year, venue, quantile_cont(nref, 0.5) med, count(*) n from p group by 1,2""")
c.execute("""create table tag as select p.*, q.med, q.n as venue_papers,
    case when p.nref <= 4 or p.nref < 0.35 * q.med then 1 else 0 end as truncated
  from p join q on q.year = p.year and q.venue = p.venue""")
t = c.execute("""select year, count(*) papers, sum(truncated) trunc_papers,
    round(100.0*sum(truncated)/count(*),1) pct_trunc,
    round(avg(nref),1) mean_all,
    round(avg(case when truncated = 0 then nref end),1) mean_clean,
    round(median(case when truncated = 0 then nref end),1) med_clean
  from tag group by 1 order by 1""").df()
t['smooth_growth_x'] = (t.mean_clean / t.mean_clean.iloc[0]).round(2)
print(t.to_string(index=False))
t.to_csv(os.path.join(OUT, 'ir_deflator_truncation.csv'), index=False)

print('\n--- per year, is the truncated share concentrated in particular venues? ---')
print(c.execute("""select year, venue, count(*) n, sum(truncated) trunc, round(median(nref),1) med
  from tag where truncated = 1 group by 1,2 having sum(truncated) >= 10 order by 1,4 desc""").df().to_string(index=False))

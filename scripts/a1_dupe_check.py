"""A1's count of citations vs the count of DISTINCT citing papers.

`edges` contains duplicate rows: 1,316 (cited, citing) pairs appear twice and 18 three times, so a
paper cited twice by the same paper counts twice in A1. This prints A1 both ways, and the rank
correlation between them, so the size of the artefact is on record. Run from C:/ranking_data:
  python -X utf8 <repo>/scripts/a1_dupe_check.py
"""
import pandas as pd
from scipy.stats import spearmanr
from rank_lib import connect
import approaches as A

OUT = A.REPO + '/results/metrics'
c = connect('4G'); A.setup(c)
d = c.execute("select cited, citing, count(*) n from edges group by 1,2 having count(*) > 1").df()
print('(cited, citing) pairs with duplicate edges:', len(d))
print(d.n.value_counts().to_string())

fut = A.outcome(c)
a_with = A.a1(c)
c.execute("drop table if exists edges_full")
c.execute("create table edges_full as select * from edges")
c.execute("drop table edges")
c.execute("create table edges as select distinct cited, citing, y_cited, y_citing from edges_full")
a_dist = A.a1(c)
c.execute("drop table edges")
c.execute("create table edges as select * from edges_full")
A.a1(c)   # leave the session with the original A1 in place

ev = pd.DataFrame([A.evaluate('A1 duplicate edges counted', a_with, fut, c),
                   A.evaluate('A1 distinct citing papers', a_dist, fut, c)])
ev.to_csv(OUT + f'/{A.FIELD}_a1_dupe.csv', index=False)
print('\n' + ev.to_string(index=False))
m = a_with.merge(a_dist, on='author', suffixes=('_dup', '_dist'))
print('\nrho between the two A1 versions: %.6f  (n=%d)' % (spearmanr(m.score_dup, m.score_dist)[0], len(m)))
print('top100 overlap: %d' % len(set(m.nlargest(100, 'score_dup').author) & set(m.nlargest(100, 'score_dist').author)))
diff = c.execute(f"""select count(*) n_papers, sum(n) edges_dup, count(*) filter (where n > 1) affected from (
    select cited, citing, count(*) n from edges_full group by 1,2 having count(*) > 1)""").df()
print('\nin-window maturity of the affected pairs:')
print(c.execute(f"""select count(*) pairs, count(*) filter (where y_citing <= y_cited + {A.DELTA}
     and y_cited between {A.BIRTH_MIN} and {A.CUTOFF}) in_window from (
     select cited, citing, min(y_cited) y_cited, min(y_citing) y_citing from edges_full
     group by 1,2 having count(*) > 1)""").df().to_string(index=False))

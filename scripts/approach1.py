"""Approach 1: windowed field-citation share -> author ranking.
usage: python -I approach1.py --field cs --delta 5 --tcut 2015 --out data/a1_cs_d5_t2015.csv
share(p) = cites(p, [y_p, y_p+delta]) / cites_F([y_p, y_p+delta]); author score = sum of share/n_authors, y_p <= tcut.
Only arXiv-internal edges (cited paper has an arXiv id, hence metadata) are used."""
import argparse, duckdb
ap = argparse.ArgumentParser()
ap.add_argument('--field', default='cs', help='primary-category prefix, e.g. cs, cs.LG, math')
ap.add_argument('--delta', type=int, default=5)
ap.add_argument('--tcut', type=int, default=2015)
ap.add_argument('--min_papers', type=int, default=3)
ap.add_argument('--out', required=True)
a = ap.parse_args()
con = duckdb.connect(); con.execute("set memory_limit='2GB'")
con.execute("create view meta as select * from read_parquet('data/meta.parquet')")
con.execute("create view papers as select * from read_parquet('data/unarxive/papers_*.parquet')")
con.execute("create view edges as select * from read_parquet('data/unarxive/edges_*.parquet') where cited_arxiv is not null")
con.execute(f"""
create table e as
 select e.cited_arxiv as cited, m.year as y_cited, c.year as y_citing
 from edges e
 join meta m on m.id = e.cited_arxiv and (m.primary_cat = '{a.field}' or m.primary_cat like '{a.field}.%')
 join papers c on c.paper_id = e.citing
 where c.year is not null and m.year is not null and c.year >= m.year""")
con.execute("create table tf as select y_citing y, count(*) n from e group by 1")
# denominator per birth year: citations into the field during [y, y+delta]
con.execute(f"""
create table den as select b.y, sum(t.n) d from (select distinct y_cited y from e) b
 join tf t on t.y between b.y and b.y + {a.delta} group by 1""")
con.execute(f"""
create table ps as
 select e.cited, e.y_cited, count(*) filter (where e.y_citing <= e.y_cited + {a.delta}) c, any_value(d.d) d
 from e join den d on d.y = e.y_cited where e.y_cited <= {a.tcut} group by 1,2""")
con.execute("create table share as select cited, y_cited, c, c*1.0/d s from ps")
con.execute(f"""
create table res as
 select author, sum(s/n) score, count(*) n_papers, sum(c) raw_cites
 from (select sh.cited, sh.s, sh.c, unnest(m.authors) author, len(m.authors) n from share sh join meta m on m.id = sh.cited)
 group by 1 having count(*) >= {a.min_papers}""")
con.execute(f"copy (select row_number() over (order by score desc) rank, author, score, n_papers, raw_cites from res order by score desc) to '{a.out}' (header, delimiter ',')")
print(con.execute("select count(*) from res").fetchone(), 'authors ranked ->', a.out)

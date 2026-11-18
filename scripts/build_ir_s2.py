"""Builds work/irs2_{edges,authors,citing_authors}.parquet from ir_s2/s2_papers.parquet (Semantic Scholar graph of the same IR papers).
Run from C:/ranking_data:  python <repo>/scripts/build_ir_s2.py"""
from rank_lib import connect, WORK
c = connect()
c.execute("create table p as select s2id, year, author_ids as aid, refs from read_parquet('C:/ranking_data/ir_s2/s2_papers.parquet') where year is not null")
c.execute(f"""copy (select r.cited, e.s2id as citing, r.y_cited, e.year as y_citing from
  (select s2id, year, unnest(refs) as cited_id from p) e
  join (select s2id as cited, year as y_cited, s2id from p) r on r.s2id = e.cited_id
  where e.year >= r.y_cited and e.s2id <> r.cited) to '{WORK}/irs2_edges.parquet' (format parquet)""")
c.execute(f"""copy (select s2id as paper, year, a as author, len(aid) as n from (select s2id, year, aid, unnest(aid) as a from p) where a is not null)
  to '{WORK}/irs2_authors.parquet' (format parquet)""")
c.execute(f"""copy (select s2id as paper, a as author from (select s2id, unnest(aid) as a from p) where a is not null and s2id in
  (select distinct citing from read_parquet('{WORK}/irs2_edges.parquet'))) to '{WORK}/irs2_citing_authors.parquet' (format parquet)""")
for t in ('edges','authors'):
    print(t, c.execute(f"select count(*) from read_parquet('{WORK}/irs2_{t}.parquet')").fetchone())
print(c.execute(f"select count(distinct author), count(distinct paper) from read_parquet('{WORK}/irs2_authors.parquet')").fetchone())
print('oa edges', c.execute(f"select count(*) from read_parquet('{WORK}/ir_edges.parquet')").fetchone())

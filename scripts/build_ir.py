"""Builds work/{name}_{edges,authors,citing_authors}.parquet from the OpenAlex pull ir/works.parquet.
Run from C:/ranking_data:  python <repo>/scripts/build_ir.py [name]   (default name: ir)"""
import sys
from rank_lib import connect, WORK
name = sys.argv[1] if len(sys.argv) > 1 else 'ir'
c = connect()
c.execute("""create table w as select id, year, author_ids, refs from read_parquet('ir/works.parquet')
             where type in ('conference-paper','article') and year is not null""")
c.execute(f"""copy (select r.ref as cited, w.id as citing, t.year as y_cited, w.year as y_citing
  from (select id, year, unnest(refs) as ref from w) r join w on w.id = r.id
  join w t on t.id = r.ref where w.year >= t.year and w.id <> r.ref) to '{WORK}/{name}_edges.parquet' (format parquet)""")
c.execute(f"""copy (select id as paper, year, a as author, len(author_ids) as n from (select id, year, author_ids, unnest(author_ids) as a from w)
  where a is not null) to '{WORK}/{name}_authors.parquet' (format parquet)""")
c.execute(f"""copy (select id as paper, a as author from (select id, unnest(author_ids) as a from w) where a is not null) to '{WORK}/{name}_citing_authors.parquet' (format parquet)""")
for t in ('edges', 'authors', 'citing_authors'):
    print(t, c.execute(f"select count(*) from read_parquet('{WORK}/{name}_{t}.parquet')").fetchone()[0])

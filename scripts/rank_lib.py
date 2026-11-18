"""Shared helpers. Run scripts from C:/ranking_data (data lives outside OneDrive)."""
import duckdb, os
DATA = os.environ.get('RANK_DATA', 'C:/ranking_data/data')
WORK = os.environ.get('RANK_WORK', 'C:/ranking_data/work')

def connect(mem='2GB'):
    c = duckdb.connect()
    c.execute(f"set memory_limit='{mem}'"); c.execute("set threads=2"); c.execute("set preserve_insertion_order=false")
    return c

AUTHOR_KEY = "lower(split_part(a,'|',1)) || ', ' || lower(substr(split_part(a,'|',2),1,1))"

def build_base(field='cs'):
    """Writes work/{field}_edges.parquet (cited paper, citing paper, years) and work/{field}_authors.parquet."""
    c = connect()
    c.execute(f"create view meta as select * from read_parquet('{DATA}/meta.parquet')")
    c.execute(f"create view papers as select * from read_parquet('{DATA}/unarxive/papers_*.parquet')")
    c.execute(f"create view edges as select * from read_parquet('{DATA}/unarxive/edges_*.parquet') where cited_arxiv is not null")
    sel = f"(primary_cat = '{field}' or primary_cat like '{field}.%')"
    c.execute(f"""copy (
        select e.citing, e.cited_arxiv as cited, m.year as y_cited, m.primary_cat as cat, p.year as y_citing
        from edges e join meta m on m.id = e.cited_arxiv and {sel}
        join papers p on p.paper_id = e.citing
        where p.year is not null and m.year is not null and p.year >= m.year and e.citing <> e.cited_arxiv
    ) to '{WORK}/{field}_edges.parquet' (format parquet)""")
    c.execute(f"""copy (
        select id as paper, year, primary_cat as cat, {AUTHOR_KEY} as author, len(authors) as n
        from (select id, year, primary_cat, unnest(authors) as a, authors from meta where {sel}) 
    ) to '{WORK}/{field}_authors.parquet' (format parquet)""")
    # authors of the *citing* papers (for self-citation removal)
    c.execute(f"""copy (
        select id as paper, {AUTHOR_KEY} as author
        from (select m.id, unnest(m.authors) as a from meta m join (select distinct citing from read_parquet('{WORK}/{field}_edges.parquet')) x on x.citing = m.id)
    ) to '{WORK}/{field}_citing_authors.parquet' (format parquet)""")
    return c

if __name__ == '__main__':
    import sys
    build_base(sys.argv[1] if len(sys.argv) > 1 else 'cs')
    c = connect()
    f = sys.argv[1] if len(sys.argv) > 1 else 'cs'
    print(c.execute(f"select count(*), count(distinct cited), min(y_cited), max(y_cited), min(y_citing), max(y_citing) from read_parquet('{WORK}/{f}_edges.parquet')").fetchone())
    print(c.execute(f"select count(*), count(distinct author), count(distinct paper) from read_parquet('{WORK}/{f}_authors.parquet')").fetchone())

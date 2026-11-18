"""Join author names, write results/ir/*.csv (+ profile.json). Run from C:/ranking_data."""
import duckdb, json, os, pandas as pd
OUT = os.environ.get('RESULTS_OUT', 'C:/Users/chait/OneDrive/文档/Acads/SEM_7/CS6101/ranking_project/results/ir')
os.makedirs(OUT, exist_ok=True)
c = duckdb.connect()
c.execute("create table w as select * from read_parquet('ir/works.parquet') where type in ('conference-paper','article')")
names = c.execute("""select aid author, mode(nm) as name from (select unnest(author_ids) aid, unnest(author_names) nm from w) group by 1""").df()
for k in ['A1', 'A2', 'A3', 'A3r1', 'A3r2', 'A3r3', 'A3r4']:
    d = pd.read_csv(f'work/ir_rank_{k}.csv').merge(names, on='author', how='left').sort_values('score', ascending=False)
    d.insert(0, 'rank', range(1, len(d) + 1))
    d.to_csv(f'{OUT}/rank_{k}.csv', index=False)
pd.read_csv('work/ir_eval_table.csv').to_csv(f'{OUT}/eval_table.csv', index=False)
prof = dict(
    works=c.execute("select count(*) from w").fetchone()[0],
    by_venue=dict(c.execute("select venue, count(*) from w group by 1 order by 2 desc").fetchall()),
    authors=c.execute("select count(distinct a) from (select unnest(author_ids) a from w)").fetchone()[0],
    ref_rows=c.execute("select sum(len(refs)) from w").fetchone()[0],
    in_set_edges=c.execute("select count(*) from read_parquet('work/ir_edges.parquet')").fetchone()[0],
    per_year=dict(c.execute("select year, count(*) from w group by 1 order by 1").fetchall()))
json.dump(prof, open(f'{OUT}/profile.json', 'w'), indent=1)
for k in ['A1', 'A2', 'A3']:
    print(k); print(pd.read_csv(f'{OUT}/rank_{k}.csv').head(12)[['rank', 'name', 'score', 'n_papers']].to_string(index=False))
print(prof['works'], prof['authors'], prof['ref_rows'], prof['in_set_edges'])

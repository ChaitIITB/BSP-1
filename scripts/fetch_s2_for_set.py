"""For every work in ir/works.parquet: get its DOI from OpenAlex, then paperId/year/authors/references from the Semantic Scholar batch API.
usage (from C:/ranking_data): OPENALEX_KEY=... python fetch_s2_for_set.py ir ir_s2 [S2_API_KEY via env S2_KEY, optional]
Writes <out>/doi.parquet and <out>/s2_papers.parquet (resumable via <out>/s2_raw.jsonl)."""
import os, sys, json, time, requests, duckdb
import pyarrow as pa, pyarrow.parquet as pq
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
oak, s2k = os.environ.get('OPENALEX_KEY'), os.environ.get('S2_KEY')
con = duckdb.connect()
ids = [r[0] for r in con.execute(f"select id from read_parquet('{src}/works.parquet') where type in ('conference-paper','article')").fetchall()]
dp = f'{out}/doi.parquet'
if not os.path.exists(dp):
    doi = {}
    for i in range(0, len(ids), 50):
        p = {"filter": "openalex_id:" + "|".join(ids[i:i+50]), "per-page": 50, "select": "id,doi"}
        if oak: p["api_key"] = oak
        for t in range(5):
            r = requests.get("https://api.openalex.org/works", params=p, timeout=60)
            if r.status_code == 200: break
            time.sleep(2 ** t)
        for x in r.json()['results']:
            if x.get('doi'): doi[x['id'].split('/')[-1]] = x['doi'].replace('https://doi.org/', '')
    pq.write_table(pa.table({'id': list(doi), 'doi': list(doi.values())}), dp)
    print('dois', len(doi), 'of', len(ids), flush=True)
doi = dict(con.execute(f"select id, doi from read_parquet('{dp}')").fetchall())
raw = f'{out}/s2_raw.jsonl'
done = set()
if os.path.exists(raw):
    for l in open(raw, encoding='utf-8'): done.add(json.loads(l)['oa'])
todo = [(i, d) for i, d in doi.items() if i not in done]
FIELDS = "paperId,year,citationCount,referenceCount,authors.authorId,authors.name,externalIds,references.paperId,references.year"
H = {"x-api-key": s2k} if s2k else {}
BS = 100
with open(raw, 'a', encoding='utf-8') as f:
    for b in range(0, len(todo), BS):
        chunk = todo[b:b+BS]
        for t in range(10):
            r = requests.post(f"https://api.semanticscholar.org/graph/v1/paper/batch?fields={FIELDS}",
                              json={"ids": ["DOI:" + d for _, d in chunk]}, headers=H, timeout=120)
            if r.status_code == 200: break
            time.sleep(min(60, 5 * (t + 1)))
        else:
            print('failed batch', b, r.status_code, flush=True); continue
        for (oa, d), rec in zip(chunk, r.json()):
            f.write(json.dumps({'oa': oa, 'doi': d, 's2': rec}) + '\n')
        f.flush()
        if (b // BS) % 10 == 0: print('batch', b // BS, 'of', len(todo) // BS + 1, flush=True)
rows = []
for l in open(raw, encoding='utf-8'):
    j = json.loads(l); s = j['s2']
    if not s: continue
    rows.append((j['oa'], s['paperId'], s.get('year'), s.get('citationCount'), s.get('referenceCount'),
                 [a.get('authorId') for a in s.get('authors') or []], [a.get('name') for a in s.get('authors') or []],
                 [x['paperId'] for x in s.get('references') or [] if x.get('paperId')]))
cols = ['oa', 's2id', 'year', 'cited_by', 'ref_count', 'author_ids', 'author_names', 'refs']
pq.write_table(pa.table({c: pa.array(v) for c, v in zip(cols, zip(*rows))}), f'{out}/s2_papers.parquet', compression='zstd')
print('s2 papers', len(rows))

"""Stream unarXive tar.xz -> papers.parquet + edges.parquet (no full extraction to disk).
usage: python -I extract_unarxive.py <tar.xz> <outdir> [max_papers]
"""
import lzma, tarfile, sys, os, re
import orjson, pyarrow as pa, pyarrow.parquet as pq
from multiprocessing import Pool

def arxiv_year(aid):
    if not aid: return None
    m = re.match(r'^(\d{2})(\d{2})\.\d{4,5}', aid)           # new style YYMM.NNNN
    if not m: m = re.match(r'^[a-z\-\.]+/(\d{2})(\d{2})\d{3}', aid)  # old style cat/YYMMNNN
    if not m: return None
    yy = int(m.group(1)); return 1900+yy if yy >= 91 else 2000+yy

def parse(line):
    d = orjson.loads(line)
    md = d.get('metadata') or {}
    pid = d['paper_id']
    vers = md.get('versions') or []
    created = vers[0]['created'] if vers else None
    paper = (pid, arxiv_year(pid), created, d.get('discipline'), md.get('categories'),
             md.get('title'), md.get('authors'), md.get('doi'), len(d.get('bib_entries') or {}))
    edges = []
    for k, b in (d.get('bib_entries') or {}).items():
        ids = b.get('ids') or {}
        a = ids.get('arxiv_id') or None
        if not a:
            c = b.get('contained_arXiv_ids') or []
            a = None
        oa = (ids.get('open_alex_id') or '').replace('https://openalex.org/', '') or None
        doi = ids.get('doi') or None
        if a or oa or doi:
            edges.append((pid, a, doi, oa, b.get('discipline')))
    return paper, edges

def lines(tarpath, limit):
    n = 0
    with open(tarpath, 'rb') as f, tarfile.open(fileobj=lzma.LZMAFile(f), mode='r|') as t:
        for m in t:
            if not (m.isfile() and m.name.endswith('.jsonl')): continue
            fh = t.extractfile(m)
            for line in fh:
                yield line; n += 1
                if limit and n >= limit: return

PS = ['paper_id','year','created','discipline','categories','title','authors','doi','n_bib']
ES = ['citing','cited_arxiv','cited_doi','cited_openalex','cited_discipline']

def flush(rows, cols, path):
    if not rows: return
    cols_data = list(zip(*rows))
    tbl = pa.table({c: pa.array(v) for c, v in zip(cols, cols_data)})
    pq.write_table(tbl, path, compression='zstd')

if __name__ == '__main__':
    tarpath, out = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    os.makedirs(out, exist_ok=True)
    P, E, shard, np_ = [], [], 0, 0
    with Pool(int(os.environ.get("WORKERS","2"))) as pool:
        for paper, edges in pool.imap(parse, lines(tarpath, limit), chunksize=8):
            P.append(paper); E.extend(edges); np_ += 1
            if len(P) >= 100000:
                flush(P, PS, f'{out}/papers_{shard:04d}.parquet'); flush(E, ES, f'{out}/edges_{shard:04d}.parquet')
                P, E, shard = [], [], shard+1
                print('papers', np_, flush=True)
    flush(P, PS, f'{out}/papers_{shard:04d}.parquet'); flush(E, ES, f'{out}/edges_{shard:04d}.parquet')
    print('done papers', np_)

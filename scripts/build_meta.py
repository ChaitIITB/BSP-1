"""Kaggle arxiv-metadata zip -> data/meta.parquet (streamed; the 4GB json is never extracted).
usage: python -I build_meta.py raw/arxiv.zip data/meta.parquet"""
import sys, zipfile, orjson, re
import pyarrow as pa, pyarrow.parquet as pq
zpath, out = sys.argv[1], sys.argv[2]
rows = []
with zipfile.ZipFile(zpath) as z:
    name = [n for n in z.namelist() if n.endswith('.json')][0]
    with z.open(name) as f:
        for line in f:
            d = orjson.loads(line)
            v = d.get('versions') or []
            m = re.search(r'(\d{4})', v[0]['created']) if v else None
            ap = d.get('authors_parsed') or []
            rows.append((d['id'], int(m.group(1)) if m else None, (d.get('categories') or '').split(' ')[0],
                         d.get('categories'), d.get('title'),
                         ['|'.join(a[:2]) for a in ap], d.get('doi')))
cols = ['id','year','primary_cat','categories','title','authors','doi']
pq.write_table(pa.table({c: pa.array(x) for c, x in zip(cols, zip(*rows))}), out, compression='zstd')
print('rows', len(rows))

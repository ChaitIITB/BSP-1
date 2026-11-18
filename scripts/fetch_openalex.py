"""Fetch all works of a venue set from OpenAlex (slim fields) -> <outdir>/works.parquet
usage: OPENALEX_KEY=... python -I fetch_openalex.py <outdir> <y0> <y1> NAME=SOURCEID [NAME=SOURCEID ...]
The key comes from the environment only; it is never written to disk."""
import os, sys, time, requests
import pyarrow as pa, pyarrow.parquet as pq
B = "https://api.openalex.org"
key = os.environ.get("OPENALEX_KEY")
out, y0, y1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
venues = dict(a.split("=") for a in sys.argv[4:])
os.makedirs(out, exist_ok=True)
SEL = "id,title,publication_year,type,authorships,referenced_works,cited_by_count,primary_location"

def get(params):
    p = dict(params); 
    if key: p["api_key"] = key
    for i in range(6):
        r = requests.get(B + "/works", params=p, timeout=60)
        if r.status_code == 200: return r.json()
        if r.status_code in (429, 500, 502, 503): time.sleep(2 ** i); continue
        r.raise_for_status()
    raise RuntimeError("giving up")

rows, seen = [], set()
for name, sid in venues.items():
    cursor, n = "*", 0
    while cursor:
        j = get({"filter": f"primary_location.source.id:{sid},publication_year:{y0}-{y1}", "per-page": 200,
                 "cursor": cursor, "select": SEL})
        for w in j["results"]:
            if w["id"] in seen: continue
            seen.add(w["id"]); n += 1
            au = w.get("authorships") or []
            rows.append((w["id"].split("/")[-1], name, w.get("publication_year"), w.get("type"), w.get("title"),
                         [a["author"]["id"].split("/")[-1] for a in au if a.get("author") and a["author"].get("id")],
                         [a["author"].get("display_name") for a in au if a.get("author") and a["author"].get("id")],
                         [r.split("/")[-1] for r in (w.get("referenced_works") or [])], w.get("cited_by_count")))
        cursor = j["meta"].get("next_cursor")
    print(f"{name}: {n} works", flush=True)
cols = ["id", "venue", "year", "type", "title", "author_ids", "author_names", "refs", "cited_by"]
pq.write_table(pa.table({c: pa.array(v) for c, v in zip(cols, zip(*rows))}), f"{out}/works.parquet", compression="zstd")
print("total", len(rows), "->", f"{out}/works.parquet")

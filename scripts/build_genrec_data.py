"""Builds GenRec-style (instruction / input / output) training data for ranking researchers.
Teacher = Approach 1 score (results/ir/rank_A1.csv). Profile text has NO citation numbers: name, paper count, years, two titles.
Run from C:/ranking_data:  python <repo>/scripts/build_genrec_data.py [outdir]   -> train/val/test .jsonl"""
import os, sys, json, random, hashlib
import pandas as pd
from rank_lib import connect, WORK
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else 'C:/ranking_data/kaggle/genrec_data'
os.makedirs(OUT, exist_ok=True)
K, N = 6, {'train': 5000, 'val': 300, 'test': 800}
BMIN, BMAX = 2006, 2014

rank = pd.read_csv(f'{REPO}/results/ir/rank_A1.csv')[['author', 'score', 'n_papers', 'name']]
c = connect()
c.execute("""create table p as select id, year, title, unnest(author_ids) as author from read_parquet('ir/works.parquet')
             where type in ('conference-paper','article') and year between %d and %d""" % (BMIN, BMAX))
papers = c.execute("select author, year, title from p order by author, year, title").df()
by_author = {a: g for a, g in papers.groupby('author')}

def short(t, n=70):
    t = ' '.join(str(t).split()); return t if len(t) <= n else t[:n - 1] + '…'

prof = {}
for r in rank.itertuples():
    g = by_author[r.author]
    first, last = g.iloc[0], g.iloc[-1]
    titles = short(first.title) if len(g) == 1 or first.title == last.title else short(first.title) + '; ' + short(last.title)
    prof[r.author] = dict(name=r.name, score=r.score,
                          text=f"{r.name} ({len(g)} papers, {int(g.year.min())}-{int(g.year.max())}): {titles}")

def split_of(a):   # deterministic split by author id
    h = int(hashlib.md5(a.encode()).hexdigest(), 16) % 100
    return 'train' if h < 70 else 'val' if h < 80 else 'test'

pool = {s: [a for a in prof if split_of(a) == s] for s in N}
INSTR = ("Rank these information retrieval researchers from highest to lowest field-relative citation impact "
         "for papers published 2006-2014. Answer with the names in order, separated by ' > '.")
rng = random.Random(0)
for s, n in N.items():
    rows, seen, tries = [], set(), 0
    while len(rows) < n and tries < n * 50:
        tries += 1
        cs = rng.sample(pool[s], K)
        sc = [prof[a]['score'] for a in cs]; nm = [prof[a]['name'] for a in cs]
        if len(set(sc)) < K or len(set(nm)) < K: continue          # strict order, unique names
        key = tuple(sorted(cs))
        if key in seen: continue
        seen.add(key)
        gold = sorted(cs, key=lambda a: -prof[a]['score'])
        rows.append(dict(instruction=INSTR, input='\n'.join(prof[a]['text'] for a in cs),
                         output=' > '.join(prof[a]['name'] for a in gold),
                         cands=[prof[a]['name'] for a in cs], gold=[prof[a]['name'] for a in gold]))
    with open(f'{OUT}/{s}.jsonl', 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(s, len(rows), 'examples from', len(pool[s]), 'authors')
print(rows[0]['input']); print('->', rows[0]['output'])

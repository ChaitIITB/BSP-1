"""Approach 2, LLM-driven: give the LLM the table layout and the metric in plain words, get SQL back, run it, show how it compares to Approach 1.
Run from C:/ranking_data:  python <repo>/scripts/a2_llm.py [--mock]
--mock skips the LLM and replays the hand-written query, only to test the plumbing."""
import os, re, sys, time
from rank_lib import connect
import approaches as A
from llm_client import chat

SCHEMA = """Tables (DuckDB SQL):
  edges(cited VARCHAR, citing VARCHAR, y_cited INT, y_citing INT)   -- one row per citation; both papers are in the field
  authors(paper VARCHAR, year INT, author VARCHAR, n INT)           -- one row per (paper, author); n = number of authors of the paper"""
def spec(d, cut, bmin, mp):
    return f"""Metric: for each paper p published in year y (use only papers with {bmin} <= y <= {cut}), count the citations p receives from papers published
in years y .. y+{d}, and divide by the total number of citations that ALL papers in the field receive in those same years y .. y+{d}. That is p's share.
An author's score is the sum over their papers of share/n (n = number of authors). Papers with no citations still count as papers (share 0).
Return only authors with at least {mp} such papers. Output columns exactly: author, score, n_papers. Order by score descending.
Answer with ONE DuckDB SQL query in a ```sql code block and nothing else."""

def get_sql(prompt, mock):
    if mock:
        return open(f'{A.REPO}/sql/a2_v1.sql').read().format(DELTA=A.DELTA, CUTOFF=A.CUTOFF, MIN_PAPERS=A.MIN_PAPERS)
    out = chat([{'role': 'user', 'content': prompt}], system='You write correct DuckDB SQL.', tag='a2')
    m = re.search(r'```(?:sql)?\s*(.*?)```', out, re.S)
    return (m.group(1) if m else out).strip().rstrip(';')

if __name__ == '__main__':
    mock = '--mock' in sys.argv
    c = connect(); A.setup(c)
    prompt = SCHEMA + '\n\n' + spec(A.DELTA, A.CUTOFF, A.BIRTH_MIN, A.MIN_PAPERS)
    err, df = None, None
    for attempt in range(1, 4):
        sql = get_sql(prompt if err is None else prompt + f'\n\nYour previous query failed with: {err}\nPrevious query:\n{sql}\nFix it.', mock)
        try:
            df = c.execute(sql).df(); break
        except Exception as e:
            err = str(e)[:400]; print(f'attempt {attempt} failed: {err}')
    if df is None: sys.exit('no working query after 3 attempts')
    stamp = time.strftime('%Y%m%d_%H%M%S')
    open(f'{A.REPO}/sql/a2_{"mock" if mock else "llm"}_{stamp}.sql', 'w').write(sql)
    ref = A.a1(c); fut = A.outcome(c)
    print('rows', len(df), '| columns', list(df.columns))
    print(A.evaluate('A2 ' + ('mock' if mock else 'LLM'), df[['author', 'score']], fut, c))
    print('agreement with A1:', A.agree(ref, df[['author', 'score']]))

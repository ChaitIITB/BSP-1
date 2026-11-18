"""Approaches 1-3 + evaluation. Run from C:/ranking_data:  python <repo>/scripts/approaches.py"""
import os
import pandas as pd
from scipy.stats import spearmanr, kendalltau
from rank_lib import connect, WORK

DELTA, CUTOFF, BIRTH_MIN, MIN_PAPERS = 3, 2014, 2006, 3
FIELD = os.environ.get('RANK_FIELD', 'cs')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = ("and not exists (select 1 from authors x join cau y on y.paper = e.citing "
        "and y.author = x.author where x.paper = e.cited)")


def setup(c):
    c.execute(f"create table edges as select cited, citing, y_cited, y_citing from read_parquet('{WORK}/{FIELD}_edges.parquet')")
    c.execute(f"create table authors as select paper, year, author, n from read_parquet('{WORK}/{FIELD}_authors.parquet')")
    c.execute(f"create table cau as select * from read_parquet('{WORK}/{FIELD}_citing_authors.parquet')")
    # `authors` is rewritten inside some metrics (loops over years); keep the original aside so a
    # second metric in the same run cannot silently score against a subset.
    c.execute("drop table if exists authors0")
    c.execute("create table authors0 as select * from authors")


# ---------- Approach 1: reference implementation ----------
def a1(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    c.execute("drop table if exists a1_share")
    c.execute("drop table if exists tot_year")
    c.execute(f"""create table tot_year as
      with tot as (select y_citing as yr, count(*) as n from edges group by 1)
      select y.year, sum(t.n) as d from (select distinct year from authors0 where year between {birth_min} and {cutoff}) y
      join tot t on t.yr between y.year and y.year + {delta} group by 1""")
    c.execute("""create table a1_share as
      with pc as (select cited as paper, y_cited as year, count(*) as c from edges e
             where y_citing <= y_cited + %d and y_cited between %d and %d group by 1, 2)
      select p.paper as paper, p.year as year, p.c * 1.0 / d.d as share, p.c as c
      from pc p join tot_year d on d.year = p.year""" % (delta, birth_min, cutoff))
    # every author paper in range counts: uncited papers add 0 but still count toward min_papers
    return c.execute(f"""select a.author, sum(coalesce(s.share,0) / a.n) as score, count(*) as n_papers, sum(coalesce(s.c,0)) as raw_cites
      from authors0 a left join a1_share s on s.paper = a.paper
      where a.year between {birth_min} and {cutoff}
      group by 1 having count(*) >= {min_papers}""").df()


# ---------- new metrics: productivity normalization (see METRIC_PLAN.md) ----------
def _author_papers(c, delta, cutoff, birth_min):
    """Every author-paper row in the birth range joined to its in-window share (0 if uncited)."""
    c.execute("drop table if exists au_paper")
    c.execute(f"""create table au_paper as select a.author, a.paper, a.year, a.n, coalesce(s.share,0) as s, coalesce(s.c,0) as c
      from authors0 a left join a1_share s on s.paper = a.paper
      where a.year between {birth_min} and {cutoff}""")


def m1(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """M1: A1 total share divided by number of papers published in the range."""
    _author_papers(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(s / n) / count(*) as score, count(*) as n_papers, sum(c) as raw_cites
      from au_paper group by 1 having count(*) >= {min_papers}""").df()


def m2(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """M2: median paper share (robust to a single hit paper)."""
    _author_papers(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, median(s) as score, count(*) as n_papers, sum(c) as raw_cites
      from au_paper group by 1 having count(*) >= {min_papers}""").df()


def m3(c, k=3, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """M3: mean of the author's k best paper shares (best-work view)."""
    _author_papers(c, delta, cutoff, birth_min)
    return c.execute(f"""with r as (select author, s, n, c, row_number() over (partition by author order by s desc) as rk
        from au_paper), t as (select author, sum(s)/count(*) as score, sum(c) as raw_cites,
        (select count(*) from au_paper z where z.author = r.author) as n_papers from r where rk <= {k} group by 1)
      select * from t where n_papers >= {min_papers}""").df()


def m4(c, K=3, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """M4: M1 shrunk toward the field-wide mean share, so small denominators cannot win by luck."""
    _author_papers(c, delta, cutoff, birth_min)
    mu = c.execute("select avg(s) from au_paper").fetchone()[0]
    return c.execute(f"""select author, (count(*) * (sum(s / n) / count(*)) + {K} * {mu}) / (count(*) + {K}) as score,
        count(*) as n_papers, sum(c) as raw_cites from au_paper group by 1 having count(*) >= {min_papers}""").df()


def b1(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """B1 baseline: plain citations per paper (in-window, co-author split 1/n)."""
    _author_papers(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(c / n) / count(*) as score, count(*) as n_papers, sum(c) as raw_cites
      from au_paper group by 1 having count(*) >= {min_papers}""").df()


def b2(c, h=3, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """B2 baseline: h-like count of papers with at least h in-window citations."""
    _author_papers(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(case when c >= {h} then 1 else 0 end) * 1.0 as score,
        count(*) as n_papers, sum(c) as raw_cites from au_paper group by 1 having count(*) >= {min_papers}""").df()


# ---------- citation deflator (W1/W3, see METRIC_PLAN_DEFLATOR.md) ----------
T0 = 2021          # reference year for D(t): the outcome window 2018-2022 carries weight 1
R_MIN_YEAR = 2005  # first year with a clean reference scrape; earlier years are dropped


def deflator(c, t0=T0, r_min_year=R_MIN_YEAR, smooth=False):
    """D(t) = R(t0)/R(t) with R(t) = references per pool paper of year t.

    Written to table `deflator` (year, R, D). Returns the yearly frame for inspection.
    `smooth` is off by default: the plan fixes no smoothing, and R(t) is already smooth once the
    truncated years are dropped. Years outside [r_min_year, max] get D = NULL (cite dropped).
    """
    c.execute("drop table if exists rt_year")
    c.execute("""create table rt_year as select year, count(*) as papers, sum(len(refs)) as refs
      from read_parquet('C:/ranking_data/ir/works.parquet')
      where type in ('conference-paper','article') and year is not null group by 1""")
    c.execute("drop table if exists deflator")
    c.execute("""create table deflator as select year, refs * 1.0 / papers as R from rt_year""")
    ref = c.execute(f"select R from deflator where year = {t0}").fetchone()[0]
    c.execute(f"update deflator set R = (case when year < {r_min_year} then null else R end)")
    c.execute("alter table deflator add column D double")
    c.execute(f"update deflator set D = {ref} / R")
    return c.execute("select * from deflator order by 1").df()


def _deflated_paper_table(c, delta, cutoff, birth_min):
    """Paper-level table: in-window citations, raw and deflated, plus the deflated denominator.

    The denominator N_F is the sum of the deflator over all in-window citations in the field, so a
    share_def is a deflated share of the deflated pie (same normalisation A1 applies, on the
    deflated measure). Edges whose citing year has no R(t) are dropped and counted in `dropped`.
    """
    c.execute("drop table if exists edges_def")
    c.execute(f"""create table edges_def as select e.cited, e.citing, e.y_cited, e.y_citing,
        coalesce(d.D, 0) as D, case when d.D is null then 1 else 0 end as miss
      from edges e left join deflator d on d.year = e.y_citing
      where e.y_citing <= e.y_cited + {delta} and e.y_cited between {birth_min} and {cutoff}""")
    c.execute("drop table if exists tot_year_def")
    c.execute(f"""create table tot_year_def as
      with tot as (select y_citing as yr, sum(case when miss = 1 then 1.0 else D end) as n from edges_def group by 1)
      select y.year, sum(t.n) as d from (select distinct year from authors0 where year between {birth_min} and {cutoff}) y
      join tot t on t.yr between y.year and y.year + {delta} group by 1""")
    c.execute("drop table if exists share_def")
    c.execute(f"""create table share_def as
      with pc as (select cited as paper, y_cited as year, sum(case when D is null then 1.0 else D end) as cd,
             count(*) as c, count(*) filter (where D is not null) as c_ok
             from edges_def group by 1, 2)
      select p.paper as paper, p.year as year, p.cd as cd, p.c as c, p.c_ok as c_ok,
             p.cd / d.d as share_def
      from pc p join tot_year d on d.year = p.year""")
    # with D = 1 everywhere this must reproduce a1_share exactly: the identity test in deflator_run.py
    # compares the two tables, so the code paths differ only by the deflator.
    c.execute("drop table if exists au_paper_def")
    c.execute(f"""create table au_paper_def as select a.author, a.paper, a.year, a.n,
        coalesce(s.cd, 0) as cd, coalesce(s.c_ok, 0) as c_ok, coalesce(s.c, 0) as c,
        coalesce(s.share_def, 0) as s from authors0 a left join share_def s on s.paper = a.paper
      where a.year between {birth_min} and {cutoff}""")


def d1(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """D1: A1's total share, computed on deflated citations. The headline replacement for A1."""
    _deflated_paper_table(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(s / n) as score, count(*) as n_papers, sum(c_ok) as raw_cites
      from au_paper_def group by 1 having count(*) >= {min_papers}""").df()


def d2(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """D2: D1 per paper. M1 with the deflator: tests whether deflation fixes what division could not."""
    _deflated_paper_table(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(s / n) / count(*) as score, count(*) as n_papers, sum(c_ok) as raw_cites
      from au_paper_def group by 1 having count(*) >= {min_papers}""").df()


def b1p(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS):
    """B1': deflated citations per paper, with no field-share normalisation at all.

    The control for whether the deflator or the share does the work.
    """
    _deflated_paper_table(c, delta, cutoff, birth_min)
    return c.execute(f"""select author, sum(cd / n) / count(*) as score, count(*) as n_papers, sum(c_ok) as raw_cites
      from au_paper_def group by 1 having count(*) >= {min_papers}""").df()


# ---------- Approach 2: LLM-written SQL ----------
def a2(c, delta=DELTA, cutoff=CUTOFF, min_papers=MIN_PAPERS, path=None):
    sql = open(path or f'{REPO}/sql/a2_v1.sql').read().format(DELTA=delta, CUTOFF=cutoff, MIN_PAPERS=min_papers)
    return c.execute(sql).df()


# ---------- Approach 3: refined system ----------
def a3(c, delta=DELTA, cutoff=CUTOFF, birth_min=BIRTH_MIN, min_papers=MIN_PAPERS,
       drop_self=True, cohort_norm=True, shrink_k=5, tie='average', agg='mean'):
    selfc = SELF if drop_self else ""
    c.execute("drop table if exists a3_cnt")
    c.execute(f"""create table a3_cnt as select e.cited as paper, e.y_cited as year, count(*) as c from edges e
      where e.y_citing <= e.y_cited + {delta} and e.y_cited between {birth_min} and {cutoff} {selfc} group by 1,2""")
    base = c.execute(f"""select a.paper, a.year, a.author, a.n, coalesce(t.c,0) as c from authors0 a
        left join a3_cnt t on t.paper = a.paper where a.year between {birth_min} and {cutoff}""").df()
    papers = base.drop_duplicates('paper')[['paper', 'year', 'c']].copy()
    if cohort_norm:   # percentile among same-year papers; tie='min' puts all uncited papers at the bottom (0)
        papers['v'] = papers.groupby('year')['c'].rank(pct=True, method=tie)
        if tie == 'min':
            papers.loc[papers.c == 0, 'v'] = 0.0
    else:
        papers['v'] = papers['c'].astype(float)
    b = base.merge(papers[['paper', 'v']], on='paper')
    g = b.groupby('author').agg(n_papers=('paper', 'nunique'), raw_cites=('c', 'sum'), mean_v=('v', 'mean'))
    g = g[g.n_papers >= min_papers].copy()
    if cohort_norm and agg == 'sum':   # volume-aware: total cohort-percentile mass, no shrinkage needed
        g['score'] = g.mean_v * g.n_papers
    elif cohort_norm:   # shrink toward the field-wide mean so 3-paper authors cannot top the list on luck
        prior = papers['v'].mean() if tie == 'min' else 0.5
        g['score'] = (g.mean_v * g.n_papers + prior * shrink_k) / (g.n_papers + shrink_k)
    else:
        g['score'] = g.mean_v * g.n_papers
    return g.reset_index()[['author', 'score', 'n_papers', 'raw_cites']]


# ---------- evaluation ----------
def outcome(c, cutoff=CUTOFF, h0=2018, h1=2022):
    """Future impact: citations (no self-cites) an author's papers born <= cutoff+3 receive in [h0,h1]."""
    return c.execute(f"""select a.author, sum(1.0/a.n) as future from edges e join authors0 a on a.paper = e.cited
        where e.y_citing between {h0} and {h1} and e.y_cited <= {cutoff + 3} {SELF} group by 1""").df()


def evaluate(name, df, fut, c):
    d = df.merge(fut, on='author', how='left').fillna({'future': 0})
    age = c.execute(f"select author, avg(year) as my from authors0 where year between {BIRTH_MIN} and {CUTOFF} group by 1").df()
    d = d.merge(age, on='author')
    return dict(name=name, n=len(d),
                spearman_future=round(spearmanr(d.score, d.future)[0], 3),
                age_bias=round(spearmanr(d.score, d.my)[0], 3),   # corr with mean birth year (0 = fair)
                top10_future_mean=round(d.nlargest(10, 'score').future.mean(), 2),
                top100_future_mean=round(d.nlargest(100, 'score').future.mean(), 2),
                tie_frac=round(1 - d.score.nunique() / len(d), 3))


def agree(a, b):
    m = a.merge(b, on='author', suffixes=('_a', '_b'))
    return dict(n=len(m), spearman=round(spearmanr(m.score_a, m.score_b)[0], 3),
                kendall=round(kendalltau(m.score_a, m.score_b)[0], 3),
                top100_overlap=len(set(m.nlargest(100, 'score_a').author) & set(m.nlargest(100, 'score_b').author)))


if __name__ == '__main__':
    c = connect()
    setup(c)
    R = {'A1': a1(c), 'A2': a2(c)}
    fut = outcome(c)
    rows = [evaluate('A1 reference', R['A1'], fut, c), evaluate('A2 LLM SQL v1', R['A2'], fut, c)]
    rounds = [('A3r1', 'A3 r1 +self-cite removal', dict(drop_self=True, cohort_norm=False)),
              ('A3r2', 'A3 r2 +cohort percentile & shrinkage (ties=avg rank)', dict(drop_self=True, cohort_norm=True)),
              ('A3r3', 'A3 r3 uncited papers at the bottom, shrink to mean', dict(drop_self=True, cohort_norm=True, tie='min')),
              ('A3r4', 'A3 r4 same, but summed over papers (volume-aware)', dict(drop_self=True, cohort_norm=True, tie='min', agg='sum'))]
    for key, nm, kw in rounds:
        R[key] = a3(c, **kw)
        rows.append(evaluate(nm, R[key], fut, c))
    R['A3'] = R['A3r3']
    raw = c.execute(f"""select author, sum(case when e.cited is null then 0 else 1.0/n end) as score
        from (select a.author, a.n, a.paper from authors0 a where a.year between {BIRTH_MIN} and {CUTOFF}) a
        left join (select cited from edges where y_cited between {BIRTH_MIN} and {CUTOFF}
                   and y_citing <= y_cited + {DELTA}) e on e.cited = a.paper group by 1""").df()
    rows.append(evaluate('baseline: raw citations (same authors)', R['A3'][['author']].merge(raw, on='author'), fut, c))
    rows.append(evaluate('baseline: raw citations (all authors with 3+ papers)', raw.merge(R['A3'][['author']], on='author'), fut, c))
    ev = pd.DataFrame(rows)
    print(ev.to_string(index=False))
    ev.to_csv(f'{WORK}/{FIELD}_eval_table.csv', index=False)
    for k, v in R.items():
        v.sort_values('score', ascending=False).to_csv(f'{WORK}/{FIELD}_rank_{k}.csv', index=False)
    print('\nagreement A1 vs A2', agree(R['A1'], R['A2']))
    print('agreement A1 vs A3', agree(R['A1'], R['A3']))
    print('agreement A2 vs A3', agree(R['A2'], R['A3']))
    for k in ('A1', 'A2', 'A3'):
        print('\nTop 10', k)
        print(R[k].nlargest(10, 'score').to_string(index=False))

"""Rebuild the CS base graph from the unarXive corpus (rank_lib.build_base equivalent).

Run from C:/ranking_data:  python <repo>/scripts/build_cs_base.py
Writes work/cs_edges.parquet, cs_authors.parquet, cs_citing_authors.parquet (overwrites).
"""
import sys
sys.path.insert(0, r'C:\Users\chait\OneDrive\文档\Acads\SEM_7\CS6101\ranking_project\scripts')
from rank_lib import connect, build_base, WORK
c = build_base('cs')
print('edges', c.execute(f"select count(*), count(distinct cited), min(y_cited), max(y_cited) from read_parquet('{WORK}/cs_edges.parquet')").fetchone())
print('authors', c.execute(f"select count(*), count(distinct author), count(distinct paper) from read_parquet('{WORK}/cs_authors.parquet')").fetchone())

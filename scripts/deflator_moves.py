import sys
sys.path.insert(0, r'C:\Users\chait\OneDrive\文档\Acads\SEM_7\CS6101\ranking_project\scripts')
import approaches as A
from rank_lib import connect
import pandas as pd
pd.set_option('display.width', 250)
c = connect('4G'); A.setup(c)
A.deflator(c)
c.execute("drop table if exists nmap")
nm = c.execute("""select author, any_value(name) as name from (
  select unnest(author_ids) as author, unnest(author_names) as name
  from read_parquet('C:/ranking_data/ir/works.parquet')) group by 1""").df()
A.a1(c); A.d1(c)
a1 = A.a1(c); d1 = A.d1(c)
age = c.execute(f"select author, avg(year) as my from authors0 where year between {A.BIRTH_MIN} and {A.CUTOFF} group by 1").df()
m = a1.merge(d1, on='author', suffixes=('_a1', '_d1')).merge(nm, on='author', how='left').merge(age, on='author')
print('names matched', m.name.notna().sum(), 'of', len(m))
m['rk_a1'] = m.score_a1.rank(ascending=False, method='min').astype(int)
m['rk_d1'] = m.score_d1.rank(ascending=False, method='min').astype(int)
m['move'] = m.rk_a1 - m.rk_d1
print('\nTOP 12 by D1 with names and A1 rank:')
print(m.nsmallest(12, 'rk_d1')[['name', 'rk_a1', 'rk_d1', 'move', 'n_papers_d1', 'raw_cites_d1', 'my']].to_string(index=False))
print('\nbiggest risers into D1 top 100 (name, A1 rank, D1 rank):')
print(m[m.rk_d1 <= 100].nlargest(8, 'move')[['name', 'rk_a1', 'rk_d1', 'move']].to_string(index=False))
print('\nbiggest fallers out of A1 top 100:')
print(m[m.rk_a1 <= 100].nsmallest(8, 'move')[['name', 'rk_a1', 'rk_d1', 'move']].to_string(index=False))
print('\nby A1-rank band: median D1/A1 (cited only) and mean D1/A1')
m['band'] = pd.cut(m.rk_a1, [0, 100, 500, 1000, 1430], labels=['1-100', '101-500', '501-1000', '1001+'])
print(m.groupby('band', observed=True).apply(lambda d: pd.Series({'n': len(d),
    'median ratio': (d.score_d1 / d.score_a1.replace(0, float('nan'))).median(),
    'mean ratio': (d.score_d1[d.score_a1 > 0] / d.score_a1[d.score_a1 > 0]).mean()}), include_groups=False).round(3).to_string())
print('\ncohort by mean birth year quartile: mean D1/A1')
m['by'] = pd.qcut(m.my, 4, labels=['oldest', 'q2', 'q3', 'youngest'])
print(m.groupby('by', observed=True).apply(lambda d: pd.Series({'n': len(d),
    'mean ratio': (d.score_d1[d.score_a1 > 0] / d.score_a1[d.score_a1 > 0]).mean()}), include_groups=False).round(3).to_string())
m.to_csv(A.REPO + '/results/metrics/ir_deflator_moves.csv', index=False)

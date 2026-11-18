-- Approach 2, single shot. Prompt given to the LLM: the schema below plus the plain-language metric:
--   "For each paper p in the field, take the citations p receives within DELTA years of its publication,
--    divided by all citations the field's papers receive in that same set of years. Ignore papers published after
--    CUTOFF. Give each author the sum of their papers' shares (split equally between co-authors) and rank authors."
-- Schema: edges(cited, citing, y_cited, y_citing)  authors(paper, year, author, n)
-- Parameters substituted by the runner: 3, 2014, 3
WITH field_cites AS (
  SELECT y_citing AS yr, COUNT(*) AS total FROM edges GROUP BY y_citing
),
window_total AS (
  SELECT p.year, SUM(f.total) AS total
  FROM (SELECT DISTINCT year FROM authors) p
  JOIN field_cites f ON f.yr BETWEEN p.year AND p.year + 3
  GROUP BY p.year
),
paper_share AS (
  SELECT e.cited AS paper, e.y_cited AS year,
         COUNT(*) * 1.0 / w.total AS share
  FROM edges e JOIN window_total w ON w.year = e.y_cited
  WHERE e.y_citing - e.y_cited <= 3 AND e.y_cited <= 2014
  GROUP BY e.cited, e.y_cited, w.total
)
SELECT a.author, SUM(s.share / a.n) AS score, COUNT(*) AS n_papers
FROM paper_share s JOIN authors a ON a.paper = s.paper
GROUP BY a.author
HAVING COUNT(*) >= 3
ORDER BY score DESC;

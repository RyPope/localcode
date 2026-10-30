"""SQL fragments shared by services."""

LANGS = ("python", "java", "cpp", "kotlin")
WINDOWS = ("30d", "3m", "6m", "older", "all")
DIFFICULTIES = ("Easy", "Medium", "Hard")

# Per-problem status from user.db (attached as `u`). Expects the problems table aliased `p`.
STATUS = """case
  when exists(select 1 from u.submissions s where s.slug = p.slug and s.verdict = 'Accepted') then 'solved'
  when exists(select 1 from u.submissions s where s.slug = p.slug)
    or exists(select 1 from u.drafts d where d.slug = p.slug) then 'attempted'
  else 'todo' end"""

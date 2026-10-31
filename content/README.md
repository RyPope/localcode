# Repo-kept content

This folder holds problems, test cases and solutions that live in this repository rather than coming from an upstream dataset. On every import (first run, **Progress → Refresh content**, or `make update`) the importer merges it over the downloaded sources, and anything defined here wins.

Use it to:

- **Add a new problem**, one that isn't on LeetCode or isn't in the upstream datasets.
- **Improve an existing problem**: add a solution, add or correct test cases, or fix its title, difficulty, topics or statement.

Changes reach a running app without rebuilding: `git pull`, then **Refresh content**.

## Layout

```
content/problems/<slug>/
  problem.md                 front matter + statement (Markdown)
  tests.json                 test cases
  solutions/<NN>-<name>.md   one file per approach
```

The folder name is the problem's slug: lowercase words joined by hyphens. For an existing problem, use the slug from its URL (`two-sum` for `/problems/two-sum`). Every file is optional for an existing problem. A new problem needs all three.

### `problem.md`

```markdown
---
title: Longest Vowel Run
difficulty: Easy          # Easy, Medium or Hard
tags: [String]            # topics, as shown in the filter list
id: 9001                  # optional problem number; leave it out for new problems
compare: exact            # optional: exact (default) or any_order
---
The statement, in Markdown. Use $...$ for math.
```

For an existing problem, include only the fields you want to change. A non-empty body replaces the statement. Write statements in your own words; don't paste text from other sites.

### `tests.json`

A JSON list of cases. `args` are the function's arguments in order, and `expected` is the return value:

```json
[
  {"args": ["beautiful"], "expected": 3},
  {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}
]
```

Linked lists and binary trees use LeetCode's array and level-order forms, and an empty result is `[]`. A new problem needs at least 3 cases. For an existing problem, your cases are added to the upstream ones, and a case with the same `args` as an upstream case replaces it.

### `solutions/*.md`

````markdown
---
title: Single pass
---
How it works, in Markdown. Time complexity $O(n)$.

```python
class Solution:
    def longestVowelRun(self, s: str) -> int:
        ...
```

```java
class Solution { ... }
```
````

Write code in LeetCode's `class Solution` style, with one fenced block per language, tagged `python`, `java`, `cpp` or `kotlin`. Files are shown in name order, after any upstream solutions.

- A **new problem's** function signature comes from the first public method (one whose name doesn't start with `_`) of its Python solution, so a new problem needs one. A language becomes available to solve in once a solution includes it. Java also enables Kotlin.
- For an **existing problem**, a solution in a language the problem didn't support yet (for example its first C++ solution) adds that language, as long as the method name and parameter count match.

## Checking your change

With the stack running (`make up`):

```bash
make validate-content          # what CI runs: parse everything, run each solution on this folder's own tests
make validate-content FULL=1   # also run your solutions against the upstream tests (needs a completed import)
```

Every solution must pass every case in every language it includes. Then run **Refresh content** and try the problem in the app. Problems and solutions from this folder carry a **local** tag.

## Nothing is ever removed

A refresh never deletes anything an earlier import had: problems, solutions and test cases that disappear upstream, or from this folder, are kept. The one exception is test cases that no longer fit a problem's function signature after it changes. To really remove something, delete it here and rebuild from scratch with `docker compose down -v && docker compose up -d`. That also deletes your progress, so export it first (**Progress → Export progress**).

## Licence

Content in this folder is part of localcode and is released under its [MIT licence](../LICENSE). Contribute only material you wrote yourself.

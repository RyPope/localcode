# Architecture

## Services

| Service | Image | Network | Responsibility |
|---|---|---|---|
| `app` | `backend/Dockerfile` (Python 3.12 + built web UI) | default + `sandbox` | HTTP API, static UI, content import, judging, user data |
| `runner` | `runner/Dockerfile` (pinned toolchains) | `sandbox` only (`internal: true`) | Compile and execute submissions; return raw per-case results |

Data lives in the `localcode-data` volume mounted at `/data`:

- `content.db`: built by the importer and replaced atomically (`content.tmp` → rename).
- `user.db`: drafts and submissions, keyed by problem slug. Imports never write to it.
- `sources/`: upstream checkouts and downloads, reused on update.

## Backend layout (`backend/localcode`)

```
config.py            paths, upstream sources (+ mirrors), limits
db.py                schemas; content_session() (user.db attached as `u`) and user_session()
importer/            dataset.py · doocs.py · signatures.py · companies.py · case_filter.py
                     fetch.py (mirror fallback) · build.py (merge → content.db) · manager.py (background job)
judging/             compare.py (equality rules) · verdicts.py (pure grading) · kwargs.py
                     types.py (runner wire types) · runner_client.py (HTTP)
services/            problems · companies · judge · progress · errors
api/                 app.py (factory) · routes/ (one router per domain) · schemas.py · deps.py · static.py
tools/               validate_cases.py (maintainer tool that generates the exclusion list)
```

Dependencies point one way: `api → services → (judging, db)`, and `importer → (judging.kwargs, db)`. Services raise `ServiceError(status, message)`, and only the API layer turns that into an HTTP response. `judging.verdicts` is pure, so verdict rules are unit-tested without a runner.

## Test format

Every runnable problem stores:

- `params`: names and abstract types from the Python signature (`int`, `List[List[int]]`, `TreeNode`, …).
- `ret`: the abstract return type.
- `cases`: `[{args: [...], expected: ...}]` as JSON. Linked lists and trees use LeetCode's array and level-order forms. A null node result is `[]`.
- `examples`: argument lists parsed from the statement, used by Run.
- `compare_mode`: `exact`, or `any_order` when the statement says "in any order".

Run computes expected values by executing the dataset's Python reference solution, and caches them per input.

## Runner protocol

`POST /execute` with `{lang, code, method, params, ret, cases, timeout_ms, cpp_sig}` returns
`{compile_error, results: [{ok, value | error, stdout, ms}], timed_out, memory_kb, exit_code, stderr}`.

Each language's harness reads `cases.json` and writes one JSON line per case, flushing after each line, so partial results survive a timeout or crash:

| Language | Harness | Notes |
|---|---|---|
| Python | `harness/py_driver.py` | Converts arguments using `params` types; per-case stdout capture; 128 MB thread stack |
| Java / Kotlin | `harness/jvm/Driver.java` | Reflection over the `Solution` method's generic types; Gson; `javafx.util.Pair` provided |
| C++ | `harness/cpp_gen.py` + `cpp/lc.hpp` | Generated `main` from the C++ signature; precompiled prelude and JSON I/O object |

Limits: Run gets 2 s per case and Submit gets 10 s in total, plus a per-language start-up allowance. Memory is capped at 1 GiB of address space (Python, C++) or a 768 MB heap (JVM). Output files are capped and process counts are limited.

## Frontend layout (`web/src`)

```
api.ts               typed API client and wire types
hooks/               useWorkspace (editor/run/submit state) · useSplit · useQueryParams
components/          Header · ProblemTable · CompanyPicker · CodeEditor · TestPanel · SolutionsTab · SubmissionsTab · ui
pages/               ProblemList · CompanyIndex · CompanyPage · Workspace (lazy, with Monaco) · Progress · Setup
lib/                 icons · format · sources
```

Filters live in the URL, so every view can be linked. Server state goes through TanStack Query. Monaco is bundled locally and only loaded with the workspace.

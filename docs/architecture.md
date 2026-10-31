# Architecture

## Services

| Service | Image | Network | Responsibility |
|---|---|---|---|
| `app` | `backend/Dockerfile` (Python 3.12 + built web UI) | default (for downloads); reaches the runner via `/run/localcode/runner-*.sock` | HTTP API, static UI, content import, judging, user data |
| `runner` | `runner/Dockerfile` (pinned toolchains) | none (`network_mode: none`); serves on a Unix socket in the `runner-socket` volume | Compile and execute submissions; return raw per-case results |

Data lives in the `localcode-data` volume mounted at `/data`:

- `content.db`: built by the importer and replaced atomically (`content.tmp` → rename).
- `user.db`: drafts and submissions, keyed by problem slug. Imports never write to it.
- `sources/`: upstream checkouts and downloads, reused on update.

## Backend layout (`backend/localcode`)

```
config.py            paths, upstream sources (+ mirrors), execution limits (single source of truth)
db.py                schemas, user.db migrations, content_session() (user.db attached as `u`), user_session()
importer/            dataset.py · doocs.py · signatures.py · companies.py · case_filter.py
                     local.py (repo-kept content/) · fetch.py (mirror fallback, cached copies)
                     build.py (merge → content.db, carrying forward anything the last import had)
                     pipeline.py (fetch + build) · manager.py (background job) · __main__.py (CLI)
judging/             compare.py (equality rules) · verdicts.py (pure grading) · kwargs.py
                     types.py (runner wire types) · runner_client.py (HTTP)
services/            problems · companies · judge · progress · system · models (response types) · errors
api/                 app.py (factory) · routes/ (one router per domain) · schemas.py (requests) · deps.py · static.py
tools/               validate_content · validate_cases · openapi · smoke · sample_refs
```

Dependencies point one way: `api → services → (judging, importer, db)`, and `importer → (judging, db)`; nothing below `services` imports from it. Services raise `ServiceError(status, message)`, and only the API layer turns that into an HTTP response. `judging.verdicts` is pure, so verdict rules are unit-tested without a runner.

## Content merge

An import builds a new `content.db` in three steps:

1. **Upstream.** The dataset, doocs and company sources are joined by slug.
2. **Repo content.** `content/problems/<slug>/` (mounted read-only at `/content`) is merged on top, and its fields win. A local Python solution defines the signature of a problem that is new, has no runnable upstream version, or was local in the previous import. Local cases replace upstream cases with the same args. Local solutions are appended. Rows record their `source` (`upstream` or `local`).
3. **Carry-forward.** Anything in the previous `content.db` that the new build lacks is copied in: whole problems, solutions (by title and source), and test cases (by args). Carried cases still have to fit the current signature. Empty metadata and a lost signature are filled from the previous import too. A refresh therefore never removes content; only `docker compose down -v` does.

## Test format

Every runnable problem stores:

- `params`: names and abstract types from the Python signature (`int`, `List[List[int]]`, `TreeNode`, …).
- `ret`: the abstract return type.
- `cases`: `[{args: [...], expected: ...}]` as JSON. Linked lists and trees use LeetCode's array and level-order forms. A null node result is `[]`.
- `examples`: argument lists parsed from the statement, used by Run.
- `compare_mode`: `exact`, or `any_order` when the statement says "in any order".

Run computes expected values by executing the dataset's Python reference solution. They're cached per input, keyed by the content version, so a re-import invalidates them.

## Runner protocol

Each runner replica serves HTTP on `/run/localcode/runner-<host>.sock` (mode 0660, app group); the app discovers sockets and skips stale ones. `POST /execute` with `{lang, code, method, params, ret, cases, timeout_ms, cpp_sig}` returns
`{compile_error, results: [{ok, value | error, stdout, ms}], timed_out, memory_kb, exit_code, stderr}`.

`runner/languages.py` describes each language (source layout, compile and run commands); `runner/sandbox.py` drops privileges, applies limits and cleans up after every run; `runner/execute.py` orchestrates. Each language's harness reads `cases.json` and writes one JSON line per case, flushing after each line, so partial results survive a timeout or crash:

| Language | Harness | Notes |
|---|---|---|
| Python | `harness/py_driver.py` | Converts arguments using `params` types; per-case stdout capture; 128 MB thread stack |
| Java / Kotlin | `harness/jvm/Driver.java` | Reflection over the `Solution` method's generic types; Gson; `javafx.util.Pair` provided |
| C++ | `harness/cpp_gen.py` + `cpp/lc.hpp` | Clang 19, `-std=c++23 -O2` (as LeetCode); generated `main` from the C++ signature; precompiled prelude and JSON I/O object; stdout captured at the file-descriptor level |

Limits are defined once in `config.Limits` and sent with every request: Run gets 2 s per case and Submit 10 s in total, plus a per-language start-up allowance; memory is 1 GiB, applied as an address-space limit (Python, C++) or a heap of 75% of it (JVM). Output files are capped and the sandbox user is limited to 256 processes.

## Frontend layout (`web/src`)

```
api.ts               API client; wire types re-exported from generated/api.ts (generated from OpenAPI)
hooks/               useWorkspace (editor/run/submit state) · useAppStatus · useSplit · useQueryParams
components/          layout (PageHeader, CardHeader, Stat, Meter, SearchInput) · ui (Segmented, badges, markdown)
                     Header · ProblemTable · CompanyPicker · CodeEditor · EditorToolbar · ProblemDescription
                     TestPanel · SolutionsTab · SubmissionsTab · QueryState · ErrorBoundary
pages/               ProblemList · CompanyIndex · CompanyPage · Workspace (lazy, with Monaco) · Progress · Setup
lib/                 draftSaver · markdown · filters · retry · icons · format · sources
theme.css            design tokens and shared primitives; pages use co-located *.module.css
```

Filters live in the URL, so every view can be linked. Server state goes through TanStack Query. Monaco is bundled locally and only loaded with the workspace.

# Contributing to localcode

Thanks for helping. localcode aims to stay small, dependable and easy to run, and contributions of every size are welcome: a wrong verdict report is as useful as a new feature.

- **Questions and ideas:** open a [feature request](../../issues/new?template=feature_request.yml).
- **Bugs:** open a [bug report](../../issues/new?template=bug_report.yml). If a correct solution was rejected, use [wrong verdict](../../issues/new?template=wrong_verdict.yml) instead.
- **Security issues:** report them privately (see [SECURITY.md](SECURITY.md)).

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting set up

You need Docker (with Compose v2), Python 3.12, Node 22 and `make`.

```bash
git clone https://github.com/ryanpope/localcode.git && cd localcode
make setup     # Python venv in backend/.venv + web dependencies
make up        # full stack at http://localhost:4173 (first run imports ~200 MB of data)
make dev-web   # optional: hot-reloading UI on http://localhost:5173 against the running API
```

`make help` lists every command. Optionally, install the commit hooks with `pip install pre-commit && pre-commit install`.

## A quick tour

| Directory | What lives there |
|---|---|
| `backend/localcode/importer` | Downloads the open datasets and builds `content.db` |
| `backend/localcode/judging` | Output comparison, verdict grading (pure), and the runner client |
| `backend/localcode/services` | One module per feature; response types in `models.py` |
| `backend/localcode/api` | FastAPI app factory and thin routers |
| `runner/` | The sandbox: `languages.py`, `sandbox.py`, and a harness per language in `harness/` |
| `web/src` | React app: `pages/`, `components/`, `hooks/`, `lib/`, generated API types in `generated/` |

[docs/architecture.md](docs/architecture.md) explains how the pieces fit together and documents the runner protocol.

## Making a change

1. For anything bigger than a small fix, open an issue first so we can agree on the approach.
2. Branch from `main`, write a failing test, make it pass.
3. Run `make lint` and `make test` (CI runs the same checks, plus image builds).
4. Open a pull request. The template has a short checklist.

### Conventions

- **Tests first.** Behaviour changes come with a test that fails without the change. Backend tests use small hand-written fixtures in `backend/tests/fixtures`. **Never commit problem statements, tests or solutions copied from elsewhere** (fixtures or `content/`).
- **Keep layers apart.** Routes stay thin and logic lives in `services/`. Grading rules live in `judging/verdicts.py` and are pure. Anything user-facing that can fail raises `ServiceError`.
- **Runner changes** need a test in `runner/tests` for every language they affect.
- **API contract.** Responses are `TypedDict`s in `backend/localcode/services/models.py`. After changing one, run `make api-types` and commit `web/openapi.json` and `web/src/generated/`; CI fails if they're stale. Never edit generated files by hand.
- **Frontend.** Server state goes through TanStack Query, page filters belong in the URL (`useQueryParams`), and stateful logic goes in hooks rather than page components. Styles go in `theme.css` (shared primitives) or a co-located CSS Module; inline `style` is only for values computed at runtime.
- **user.db is precious.** Schema changes go through a new entry in `USER_MIGRATIONS` (`backend/localcode/db.py`); never edit an existing migration.
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).
- **UI changes** include before/after screenshots in the PR. If README images change, regenerate them with `make screenshots`.

## Adding problems and solutions

New problems, extra solutions and corrected test cases go in [`content/`](content/README.md) as Markdown and JSON files; that page describes the format. Run `make validate-content` with the stack up before opening the PR. CI runs the same check, which runs every solution against its tests in the sandbox. Contribute only material you wrote yourself.

## Good first contributions

- **Write solutions** for problems the upstream data has few of (Kotlin especially), in `content/`.
- **Triage wrong verdicts.** Reproduce a reported case and, if the test case itself is invalid, add it to the exclusion list.
- **Kotlin reference solutions.** The upstream dataset has very few, so the Solutions tab falls back to Java. Contributing Kotlin solutions upstream to [doocs/leetcode](https://github.com/doocs/leetcode) helps everyone.
- **Special judges** for problems that accept several valid answers (for example "return any valid arrangement").
- **Accessibility and keyboard navigation** improvements in the web app.
- **Docs**: troubleshooting tips for platforms we haven't tested (Windows, Linux distributions, low-memory machines).

## Adding a language

1. Add the toolchain to `runner/Dockerfile`, pinned to an exact version.
2. Add a harness that follows the runner protocol, and a `Language` entry in `runner/languages.py`.
3. Generate starter code in `backend/localcode/importer/signatures.py`, include the language in `build.py`'s `langs`, add it to `Lang` in `services/models.py`, and run `make api-types`.
4. Add it to `LANG_LABEL` (`web/src/api.ts`) and `MONACO_LANG` (`web/src/monaco.ts`).
5. Add runner tests mirroring `test_jvm.py` / `test_cpp.py`.

## Maintainer tasks

- **Regenerate the test-case exclusion list** after a dataset update: `make validate-cases` (about 45 minutes with three runner replicas), then commit `backend/localcode/data/excluded_cases.json`.
- **Check reference pass rates** against a scratch instance: `backend/.venv/bin/python -m localcode.tools.sample_refs -n 100`.
- **Release:** move the `Unreleased` section of [CHANGELOG.md](CHANGELOG.md) under a version heading, tag `vX.Y.Z`, and publish a GitHub release.

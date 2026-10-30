# Contributing

Thanks for helping. localcode aims to stay small, dependable and easy to run.

## Getting set up

```bash
make setup   # Python 3.12 venv in backend/.venv + web dependencies
make up      # full stack at http://localhost:4173
make dev-web # optional: hot-reloading UI on :5173 against the running API
```

Read [docs/architecture.md](docs/architecture.md) first. It covers how the services, packages and test format fit together.

## Before you open a pull request

```bash
make lint
make test
```

CI runs the same checks: ruff, ESLint, Prettier, TypeScript, backend tests, runner tests in Docker, and image builds.

## Conventions

- **Tests first.** Behaviour changes come with a test that fails without the change. Backend tests use small hand-written fixtures in `backend/tests/fixtures`. **Never commit real problem statements, tests or solutions.**
- **Keep layers apart.** Routes stay thin and logic lives in `services/`. Grading rules live in `judging/verdicts.py` and are pure. Anything user-facing that can fail raises `ServiceError`.
- **Runner changes** need a test in `runner/tests` for every supported language they affect. The harness protocol is documented in the architecture notes.
- **API contract**: responses are `TypedDict`s in `backend/localcode/services/models.py`. After changing one, run `make api-types` and commit `web/openapi.json` and `web/src/generated/`; CI fails if they are stale. Never edit generated files by hand.
- **Frontend**: server state goes through TanStack Query, page filters belong in the URL (`useQueryParams`), and stateful logic goes in hooks, not page components. Styles go in `theme.css` (shared primitives) or a co-located CSS Module; inline `style` is only for values computed at runtime.
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).

## Adding a language

1. Add the toolchain to `runner/Dockerfile`, pinned to an exact version.
2. Add a harness that follows the runner protocol, and a `Language` entry in `runner/languages.py`.
3. Generate starter code in `backend/localcode/importer/signatures.py`, include the language in `build.py`'s `langs`, add it to `Lang` in `services/models.py`, and run `make api-types`.
4. Add it to `LANG_LABEL` (`web/src/api.ts`) and `MONACO_LANG` (`web/src/monaco.ts`).
5. Add runner tests mirroring `test_jvm.py` / `test_cpp.py`.

## Regenerating the test-case exclusion list

After a dataset update, maintainers can run `make validate-cases`. It is slow: about 45 minutes with three runner replicas. Commit the resulting `backend/localcode/data/excluded_cases.json`.

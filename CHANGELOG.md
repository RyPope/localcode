# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- First public version: about 4,100 problems (2,830 runnable against 274k hidden tests), company frequency lists for 423 companies, reference solutions with explanations.
- Judging in Python 3.14, Java 25, C++23 (Clang 23) and Kotlin 2.4 in a sandboxed runner with no network access.
- Problem list, company pages, workspace with Run/Submit and custom cases, submission history, progress dashboard and export.
- One-command setup with Docker Compose; content imported from open datasets at first run, with mirror fallbacks.
- Repo-kept content in `content/`: new problems and extra solutions, tests or corrections for existing ones, checked in CI by `make validate-content` and marked "local" in the app.
- The Progress page lists every solved problem, with when it was first accepted and in which languages; the solved counts link to the filtered problem list.
- **Refresh content** never removes problems, solutions or test cases that an earlier import had.

### Changed

- Dependencies brought up to date: Clang 23 from LLVM's apt repository (was Debian's Clang 19), Node 26 LTS for the web build and CI (was 22), Gson 2.15, TanStack Query 5.105.1. The excluded test cases were regenerated with the new toolchain. TypeScript 6.0 (7 waits on typescript-eslint support).

### Fixed

- `LOCALCODE_ALLOWED_HOSTS` set when starting Docker Compose now reaches the app, so it can be served under another host name as the README describes.

### Security

- Monaco's bundled DOMPurify is pinned to our patched 3.4.17 (Monaco 0.57 pins 3.4.15, affected by several XSS advisories); `npm audit --omit=dev` reports no vulnerabilities.

- The runner has no network; the app reaches it over a group-restricted Unix socket.
- Both containers run without root privileges or unneeded capabilities, under `no-new-privileges`.
- Host-header and Origin checks, a content security policy and other security headers.
- Shared memory, message queues and semaphores a submission creates are removed after each run, and shared memory is capped at 16 MB.
- The runner reads a submission's output only through files it controls, so a submission can't redirect it to a root-only file.

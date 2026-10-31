# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- First public version: about 4,100 problems (2,830 runnable against 274k hidden tests), company frequency lists for 423 companies, reference solutions with explanations.
- Judging in Python 3.14 and Java 25 (the versions LeetCode judges with), C++23 with Clang 19 and Kotlin 2.4, in a sandboxed runner with no network access.
- Problem list, company pages, workspace with Run/Submit and custom cases, submission history, progress dashboard and export.
- One-command setup with Docker Compose; content imported from open datasets at first run, with mirror fallbacks.
- Repo-kept content in `content/`: new problems and extra solutions, tests or corrections for existing ones, checked in CI by `make validate-content` and marked "local" in the app.
- **Refresh content** never removes problems, solutions or test cases that an earlier import had.

### Security

- The runner has no network; the app reaches it over a group-restricted Unix socket.
- Both containers run without root privileges or unneeded capabilities, under `no-new-privileges`.
- Host-header and Origin checks, a content security policy and other security headers.
- Shared memory, message queues and semaphores a submission creates are removed after each run, and shared memory is capped at 16 MB.
- The runner reads a submission's output only through files it controls, so a submission can't redirect it to a root-only file.

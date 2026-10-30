# Security

localcode runs code you type on your own machine. It is designed to contain mistakes and hostile snippets, such as infinite loops, fork bombs, runaway memory and attempts to read or write outside the sandbox. It is **not** a hardened multi-tenant service: don't expose it to untrusted users or networks.

## Reporting a vulnerability

Please report security issues privately through [GitHub Security Advisories](../../security/advisories/new) rather than in a public issue. Include steps to reproduce; a submission that escapes the sandbox is the most valuable kind of report. You'll get an acknowledgement within a week.

## How submissions are contained

The **runner** container executes submissions:

- **No network.** It runs with `network_mode: none`, so there's no internet, DNS or access to the app. The app talks to it over a Unix socket in a shared volume (mode `0660`, app group only), which the sandbox user cannot open.
- **Unprivileged.** Each submission runs as uid 10001 with no supplementary groups and no capabilities, under `no-new-privileges` (setuid binaries can't elevate) and Docker's default seccomp profile.
- **Read-only.** The root filesystem is read-only. Each run gets a fresh private directory (mode `0700`).
- **Limited.** Wall-clock time, address space (or JVM heap), file size, 256 processes per sandbox user, container memory (2 GB) and PIDs (512).
- **Cleaned.** After every run the runner kills every process the sandbox user still owns and deletes its files from `/tmp` and `/dev/shm`. An init process reaps orphans.
- **Minimal privileges for the runner itself.** The root server process keeps only the capabilities it needs to prepare the sandbox and clean up: `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID` and `KILL`.

The **app** container runs as uid 1000 with no capabilities, `no-new-privileges` and a read-only root filesystem.

## Browser-facing protections

The app has no login, so it defends against other web pages instead:

- It listens only on `127.0.0.1`.
- It rejects requests whose `Host` isn't `localhost`, `127.0.0.1` or `::1`, which defeats DNS-rebinding attacks. Set `LOCALCODE_ALLOWED_HOSTS` to add names.
- It rejects state-changing requests with a foreign `Origin`, which blocks cross-site requests.
- Responses carry a Content-Security-Policy, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` and `Cross-Origin-Opener-Policy: same-origin`.
- Imported problem statements and explanations are sanitised with DOMPurify before rendering.

## Supply chain

- Dependencies are pinned, and Dependabot proposes updates.
- Toolchain downloads in the runner image (Kotlin, Gson) are verified against pinned SHA-256 checksums.
- CI actions are pinned to commit SHAs.
- Problem content is downloaded at runtime from the configured sources over HTTPS. It is rendered only after sanitisation, and the reference solutions it contains are only ever executed inside the sandbox.

## Known limitations

- Submitted code can read its own test inputs and the runner's source code, and can see the runner's process list. That only lets you cheat yourself.
- Problem statements may embed images from public CDNs, which your browser fetches directly. Referrers are not sent.
- C++ runs without AddressSanitizer, unlike LeetCode.

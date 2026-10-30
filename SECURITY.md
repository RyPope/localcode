# Security

localcode runs code you type on your own machine. The runner service is built to contain mistakes such as infinite loops, runaway memory use and accidental file writes. It is **not** a hardened multi-tenant sandbox, so don't expose localcode to untrusted users or networks.

What the runner does:

- Runs on a Docker network with no internet access (`internal: true`), and only the app can reach it.
- Executes each submission as an unprivileged user (uid 10001, no supplementary groups), in a fresh private directory (mode 0700), on a read-only root filesystem.
- Enforces wall-clock, address-space, file-size and per-user process limits (256), and kills the whole process group on timeout.
- After every run, kills any process the sandbox user still owns and deletes its temporary files, so nothing carries over into the next submission. An init process reaps orphans.
- Binds the app only to `127.0.0.1:4173` on the host.

Known limits: submitted code can reach the app's API over the internal network (it shares that network with the runner). Submissions are judged on your own machine for your own practice, so the harness doesn't try to stop code from reading its own test inputs.

If you find a way to escape these limits, or another security issue, please report it privately through GitHub Security Advisories on this repository rather than in a public issue.

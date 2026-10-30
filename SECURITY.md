# Security

localcode runs code you type on your own machine. The runner service is built to contain mistakes such as infinite loops, runaway memory use and accidental file writes. It is **not** a hardened multi-tenant sandbox, so don't expose localcode to untrusted users or networks.

What the runner does:

- Runs on a Docker network with no internet access (`internal: true`), and only the app can reach it.
- Executes each submission as an unprivileged user (uid 10001), in a fresh temporary directory, on a read-only root filesystem.
- Enforces wall-clock, address-space, file-size and process limits, and kills the whole process group on timeout.
- Binds the app only to `127.0.0.1:4173`.

If you find a way to escape these limits, or another security issue, please report it privately through GitHub Security Advisories on this repository rather than in a public issue.

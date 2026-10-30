#!/bin/sh
# Starts as root only to give /data to the unprivileged app user (volumes created by earlier
# versions are root-owned), then drops privileges for the life of the process.
set -eu
if [ "$(id -u)" = 0 ]; then
  find /data -xdev ! -user localcode -exec chown localcode:localcode {} +
  exec setpriv --reuid=localcode --regid=localcode --init-groups --inh-caps=-all "$@"
fi
exec "$@"

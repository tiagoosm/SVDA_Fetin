#!/bin/sh
# Hosts mount persistent disks owned by root. Fix ownership of the data
# directory, then drop privileges so the app never runs as root.
set -e
data_dir="$(dirname "${DATABASE_PATH:-/data/svda.db}")"
mkdir -p "$data_dir"
chown svda:svda "$data_dir" 2>/dev/null || true
exec setpriv --reuid=svda --regid=svda --init-groups "$@"

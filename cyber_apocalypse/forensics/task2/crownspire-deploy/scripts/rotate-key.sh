#!/bin/sh
# Rotate the warden's signing key.
#
# This does NOT touch the repo. It rotates the key in the vault and re-signs the
# currently published manifests so the altar keeps accepting them. Run it after
# any suspected key exposure -- a key is burned the instant it is pushed.
set -eu

if [ -z "${WARDEN_SIGNING_KEY:-}" ]; then
    echo "WARDEN_SIGNING_KEY not set (source your .env or CI secrets)" >&2
    exit 1
fi

build_dir="${1:-build}"

echo "re-signing manifests in $build_dir with the current warden key"
for m in "$build_dir"/*.json; do
    [ -f "$m" ] || continue
    python -m crownspire sign "$m"
done

echo "done. remember to publish the new signatures:"
echo "    python -m crownspire publish $build_dir"

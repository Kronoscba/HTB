#!/bin/sh
# verify every manifest/signature pair in a build dir
set -e
dir="${1:-build}"
for m in "$dir"/*.json; do
    [ -f "$m" ] || continue
    sig="$m.sig"
    if [ ! -f "$sig" ]; then
        echo "MISSING SIG: $m"
        exit 1
    fi
    python -m crownspire verify "$m" "$sig"
done
echo "all manifests verified"

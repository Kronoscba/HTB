#!/bin/sh
# publish signed sigil manifests to the Crownspire reliquary.
# creds come from the environment (CI secret store or local .env) -- never hard-code them.
set -e

: "${RELIQUARY_ENDPOINT:?set RELIQUARY_ENDPOINT}"
: "${RELIQUARY_BUCKET:?set RELIQUARY_BUCKET}"

sync() {
    aws --endpoint-url "$RELIQUARY_ENDPOINT" s3 sync ./build "s3://$RELIQUARY_BUCKET/"
}

echo "sealing manifests -> $RELIQUARY_BUCKET"
# the reliquary 403s on the first touch after a key rotation; retry once
sync || { echo "retrying after 403..."; sleep 2; sync; }
echo "done"

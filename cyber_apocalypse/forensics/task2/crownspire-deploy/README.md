# crownspire-deploy

Cinderbound tooling to sign and publish **sigil manifests** to the Crownspire
reliquary before a binding rite. The reliquary is an S3-compatible store; every
manifest is signed with the wardens' key so the priesthood can verify
provenance at the altar.

## Install

    python -m pip install -e ".[dev]"

## Usage

    crownspire validate examples/dawn-rite.json
    crownspire sign build/manifest.json
    crownspire publish build/
    crownspire altar build/          # re-verify a published set (altar gate)

Credentials are read from the environment. For local development, copy
`.env.example` to `.env` (untracked) and the CLI will load it automatically;
pass `--env-file PATH` to point elsewhere.

See `docs/manifest-format.md` for the schema, `docs/deploy.md` for the deploy
flow, and `docs/architecture.md` for how the pieces fit together.

## Credentials

Credentials never live in the repo. In CI they come from the secret store
(see `.github/workflows/deploy.yml`); locally they come from an untracked
`.env`. If you ever see a `.env` or `*.creds` file tracked here, something has
gone wrong -- rotate the warden's key immediately (`scripts/rotate-key.sh`) and
scrub it from history. See `SECURITY.md`.

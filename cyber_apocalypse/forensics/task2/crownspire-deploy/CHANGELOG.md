# Changelog

## [0.3.0] - 2026-05-28

### Added
- `crownspire altar` re-verifies a published set the way the altar does
- local `.env` support via a tiny built-in dotenv loader (`--env-file`)
- `docs/architecture.md`, `SECURITY.md`, `CODEOWNERS`
- `scripts/rotate-key.sh` and an `ashmarch` example manifest

### Changed
- `deploy.sh` loads credentials from the environment and retries once on a 403
- signing key and reliquary creds now come solely from CI secrets / local `.env`

### Fixed
- `deploy.sh` used `RELIQUARY_URL`; corrected to `RELIQUARY_ENDPOINT`

## [0.2.0] - 2026-05-24

### Added
- CI workflow (lint + test matrix) and tag-triggered publish workflow
- `docs/manifest-format.md` and `docs/deploy.md`
- `scripts/verify-all.sh`, `scripts/new-manifest.py`
- example manifests under `examples/`

## [0.1.0] - 2026-05-19

### Added
- initial reliquary deployer skeleton
- manifest model with validation
- HMAC signing + detached signature files
- `crownspire` CLI (`validate`, `sign`, `verify`, `publish`)
- reliquary client over the `aws` CLI

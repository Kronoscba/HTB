# Deploying manifests

## Local

1. `cp .env.example .env` and fill in the warden's key material. **Never commit
   `.env`.** It is gitignored; keep it that way.
2. Build your manifests into `build/` (one `.json` per rite).
3. `python -m crownspire publish build/` -- signs each manifest and syncs the
   directory to the reliquary.

## CI

Tagging a release (`git tag v1.2.3 && git push --tags`) triggers
`.github/workflows/deploy.yml`. All credentials come from repository secrets:

| secret                | maps to env                 |
|-----------------------|-----------------------------|
| `RELIQUARY_ENDPOINT`  | `RELIQUARY_ENDPOINT`        |
| `RELIQUARY_BUCKET`    | `RELIQUARY_BUCKET`          |
| `RELIQUARY_KEY_ID`    | `AWS_ACCESS_KEY_ID`         |
| `RELIQUARY_SECRET`    | `AWS_SECRET_ACCESS_KEY`     |
| `WARDEN_SIGNING_KEY`  | `WARDEN_SIGNING_KEY`        |

## The 403 on first push

After a warden key rotation the gateway returns `403` on the very first request
while it warms its cache. `deploy.sh` retries once after a short pause. If it
keeps failing, the key is genuinely wrong -- rotate again from the vault, do not
paste keys into the repo to test.

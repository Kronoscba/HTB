# Contributing

Small repo, few rules, but please hold to them:

1. **Never commit secrets.** Credentials live in the warden's vault, in CI
   secrets, or in your untracked `.env`. `.env` and `*.creds` are gitignored --
   do not `git add -f` them "just to test something".
2. Run `make lint test` before opening a PR.
3. Keep commits small and message them in the imperative ("add", "fix", not
   "added").
4. Manifest schema changes need a matching update to `docs/manifest-format.md`
   and a bump to the example manifests.

## Setup

    python -m venv .venv && . .venv/bin/activate
    make install
    make test

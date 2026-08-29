# Security policy

## Reporting

Found something? Mail the wardens at `security@crownspire.valyssar`. Do not open
a public issue for anything that touches the reliquary or the signing key.

## Handling credentials

- The warden's signing key and the reliquary access keys are **secrets**. They
  live in the warden's vault, in CI repository secrets, and (locally, for
  development only) in an untracked `.env`.
- `.env` and `*.creds` are gitignored. Never `git add -f` them.
- If a secret ever lands in a commit:
  1. **Rotate it immediately** -- assume it is burned the moment it is pushed.
  2. Scrub it from history (`git filter-repo` / BFG) and force-push.
  3. Remember that rewriting history does **not** delete the old objects until
     a `gc`/`prune` runs. A pushed secret must be rotated regardless.

## Signatures

Every manifest is signed with HMAC-SHA256 over its canonical form. The altar
refuses to bind any rite whose manifest fails verification or arrives unsigned.

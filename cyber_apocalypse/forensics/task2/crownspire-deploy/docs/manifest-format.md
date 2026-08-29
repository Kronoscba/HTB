# Sigil manifest format

A manifest is a small JSON document describing the sigils that make up a rite.

```json
{
  "name": "dawn-rite",
  "realm": "crownspire",
  "revision": 3,
  "sigils": [
    { "id": "ember", "order": 1, "binding": "oath" },
    { "id": "brine", "order": 2, "binding": "seal" }
  ]
}
```

## Fields

| field      | type   | notes                                             |
|------------|--------|---------------------------------------------------|
| `name`     | string | rite name, kebab-case                             |
| `realm`    | string | one of `valyssar`, `crownspire`, `ashmarch`       |
| `revision` | int    | monotonic, starts at 1                            |
| `sigils`   | array  | each has `id`, `order` (unique), `binding`        |

## Signing

The signature is `HMAC-SHA256(warden_key, canonical_bytes)` in hex, where
`canonical_bytes` is the manifest serialized with sorted keys and sigils sorted
by `order`. Because the canonical form is order-independent, re-formatting the
JSON on disk never changes the signature.

Signatures are written to a detached `<manifest>.sig` next to the manifest and
uploaded alongside it. The altar refuses to bind a rite whose signature does
not verify.

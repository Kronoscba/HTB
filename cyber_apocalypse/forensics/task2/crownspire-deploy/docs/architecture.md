# Architecture

`crownspire-deploy` is small on purpose. The pieces:

```
        +-------------+     sign      +-------------+
manifest| manifest.py | ------------> |  signing.py |
 (json) +------+------+  canonical    +------+------+
               |            bytes            |
               v                             v
        +-------------+              <manifest>.sig
        |   cli.py    |
        +------+------+
               | publish
               v
        +-------------+   aws s3 sync  +----------------+
        | reliquary.py| -------------> | Crownspire     |
        +-------------+                | reliquary (S3) |
                                       +----------------+
                                               |
                                        altar re-verifies
                                       (altar.py) before a rite
```

## Modules

| module          | responsibility                                            |
|-----------------|-----------------------------------------------------------|
| `manifest.py`   | model + validation + canonical byte serialization         |
| `signing.py`    | HMAC-SHA256 sign / verify / write detached signature       |
| `config.py`     | read + validate required environment                       |
| `dotenv.py`     | load a local `.env` for development                        |
| `reliquary.py`  | thin wrapper over the `aws` CLI (S3-compatible endpoint)   |
| `altar.py`      | re-verify a published set (the last gate before binding)   |
| `cli.py`        | argument parsing + command dispatch                        |
| `utils.py`      | small filesystem/hash helpers                              |

## Why the canonical form

Signing the raw file bytes would make a signature break every time someone
re-indented the JSON. Instead we sign a canonical representation (sorted keys,
sigils sorted by `order`, fixed separators), so formatting churn never
invalidates a good signature.

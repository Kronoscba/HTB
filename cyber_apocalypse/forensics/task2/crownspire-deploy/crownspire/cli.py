"""Command-line entry point for crownspire-deploy.

Subcommands:

    crownspire validate <manifest>         check a manifest parses + validates
    crownspire sign <manifest> [-o SIG]    write a detached HMAC signature
    crownspire verify <manifest> <sig>     verify a manifest against a signature
    crownspire publish <build-dir>         sign + push signed manifests to the reliquary
    crownspire altar <build-dir>           re-verify a published set the way the altar does

Credentials come from the environment (see crownspire.config).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__
from .altar import all_ok, verify_dir
from .config import Config
from .dotenv import load_dotenv
from .errors import CrownspireError
from .manifest import load_manifest
from .reliquary import Reliquary
from .signing import verify_manifest, write_signature


def _cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    print(f"ok: {manifest.name} rev {manifest.revision} "
          f"({len(manifest.sigils)} sigils, realm {manifest.realm})")
    return 0


def _cmd_sign(args: argparse.Namespace) -> int:
    config = Config.from_env()
    manifest = load_manifest(args.manifest)
    sig_path = args.output or (args.manifest + ".sig")
    signature = write_signature(manifest, config.signing_key_bytes, sig_path)
    print(f"signed {args.manifest} -> {sig_path}")
    print(signature)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    config = Config.from_env()
    manifest = load_manifest(args.manifest)
    with open(args.signature, "r", encoding="utf-8") as fh:
        signature = fh.read()
    if verify_manifest(manifest, config.signing_key_bytes, signature):
        print("signature OK")
        return 0
    print("signature MISMATCH", file=sys.stderr)
    return 2


def _cmd_publish(args: argparse.Namespace) -> int:
    config = Config.from_env()
    reliquary = Reliquary(config)
    # sign every manifest in the build dir, then sync the whole tree up
    signed = 0
    for name in sorted(os.listdir(args.build_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(args.build_dir, name)
        manifest = load_manifest(path)
        write_signature(manifest, config.signing_key_bytes, path + ".sig")
        signed += 1
    print(f"signed {signed} manifest(s), syncing -> {config.bucket}")
    reliquary.sync(args.build_dir, prefix=args.prefix)
    print("done")
    return 0


def _cmd_altar(args: argparse.Namespace) -> int:
    config = Config.from_env()
    results = verify_dir(args.build_dir, config.signing_key_bytes)
    for r in results:
        status = "OK" if r.ok else f"REFUSED ({r.reason})"
        print(f"  {r.manifest}: {status}")
    if all_ok(results):
        print("altar: all manifests verified, rite may bind")
        return 0
    print("altar: refusing to bind, one or more manifests failed", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crownspire",
                                     description="Cinderbound reliquary deployer")
    parser.add_argument("--version", action="version",
                        version=f"crownspire {__version__}")
    parser.add_argument("--env-file", default=".env",
                        help="dotenv file to load before running (default: .env)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate a manifest")
    p_validate.add_argument("manifest")
    p_validate.set_defaults(func=_cmd_validate)

    p_sign = sub.add_parser("sign", help="sign a manifest")
    p_sign.add_argument("manifest")
    p_sign.add_argument("-o", "--output", help="signature path (default: <manifest>.sig)")
    p_sign.set_defaults(func=_cmd_sign)

    p_verify = sub.add_parser("verify", help="verify a manifest signature")
    p_verify.add_argument("manifest")
    p_verify.add_argument("signature")
    p_verify.set_defaults(func=_cmd_verify)

    p_publish = sub.add_parser("publish", help="sign + publish a build dir")
    p_publish.add_argument("build_dir")
    p_publish.add_argument("--prefix", default="manifests", help="key prefix in the bucket")
    p_publish.set_defaults(func=_cmd_publish)

    p_altar = sub.add_parser("altar", help="re-verify a published set (altar gate)")
    p_altar.add_argument("build_dir")
    p_altar.set_defaults(func=_cmd_altar)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Populate the environment from a local dotenv if present. In CI there is
    # none and the secret store has already set everything -- load_dotenv is a
    # no-op in that case and never overrides an existing value.
    load_dotenv(args.env_file)
    try:
        return args.func(args)
    except CrownspireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

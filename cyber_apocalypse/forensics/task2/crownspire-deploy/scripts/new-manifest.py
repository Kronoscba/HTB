#!/usr/bin/env python3
"""Scaffold a new sigil manifest.

    scripts/new-manifest.py dusk-rite --realm crownspire > build/dusk-rite.json
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--realm", default="crownspire")
    ap.add_argument("--revision", type=int, default=1)
    args = ap.parse_args()

    manifest = {
        "name": args.name,
        "realm": args.realm,
        "revision": args.revision,
        "sigils": [
            {"id": "ember", "order": 1, "binding": "oath"},
        ],
    }
    json.dump(manifest, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

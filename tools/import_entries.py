#!/usr/bin/env python3
"""Import entries from CSV or JSON into content/terms.json.

Defaults to a dry run: it reports what would change, row by row, and writes nothing.
Reviewed records (approved or published) are never overwritten silently - the import
refuses them unless --allow-reviewed is given, which is itself recorded in the output.

    python3 tools/import_entries.py incoming.csv            # dry run
    python3 tools/import_entries.py incoming.csv --apply
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS = ROOT / "content" / "terms.json"
LIST_FIELDS = ("synonyms", "subjects", "related", "references")
PROTECTED = {"approved", "published"}


def read_rows(path: Path):
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for key in LIST_FIELDS:
            if key in r and isinstance(r[key], str):
                r[key] = [x.strip() for x in r[key].split(";") if x.strip()]
        if "revision" in r and str(r["revision"]).isdigit():
            r["revision"] = int(r["revision"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--allow-reviewed", action="store_true",
                    help="permit overwriting approved or published records")
    args = ap.parse_args()

    current = json.loads(TERMS.read_text(encoding="utf-8"))
    by_slug = {e["slug"]: e for e in current}
    rows = read_rows(Path(args.source))

    created, updated, refused, invalid = [], [], [], []
    for i, r in enumerate(rows, start=1):
        slug = (r.get("slug") or "").strip()
        if not slug:
            invalid.append("row %d: no slug" % i)
            continue
        if slug not in by_slug:
            created.append(slug)
            if args.apply:
                current.append(r)
            continue
        existing = by_slug[slug]
        if existing.get("editorial_state") in PROTECTED and not args.allow_reviewed:
            refused.append("row %d (%s): record is %s; refused to overwrite reviewed content"
                           % (i, slug, existing["editorial_state"]))
            continue
        updated.append(slug)
        if args.apply:
            existing.update(r)
            existing["revision"] = int(existing.get("revision", 1)) + 1

    print("source rows: %d" % len(rows))
    print("would create: %d" % len(created))
    print("would update: %d" % len(updated))
    for line in refused + invalid:
        print("REFUSED " + line if line in refused else "INVALID " + line)
    if args.apply:
        TERMS.write_text(json.dumps(current, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied; re-run tools/validate.py and tools/build.py")
    else:
        print("dry run - nothing written. Re-run with --apply to commit these changes.")
    return 1 if invalid else 0


if __name__ == "__main__":
    sys.exit(main())

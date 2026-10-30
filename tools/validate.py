#!/usr/bin/env python3
"""Validate the entry corpus before building or publishing.

Checks the content model in section 5.1 of the project brief and the publication
rules in section 7.2. Exits non-zero if any entry fails, printing one line per
defect so the report is row-level rather than a single pass/fail.

    python3 tools/validate.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"

RANGES = {"plain_definition": (40, 80), "technical_explanation": (100, 250),
          "practical_example": (40, 90), "common_misunderstanding": (30, 80)}
REQUIRED = ["entry_id", "slug", "term", "plain_definition", "technical_explanation",
            "practical_example", "common_misunderstanding", "subjects", "references",
            "editorial_state", "revision", "created", "updated", "language"]
STATES = {"draft", "submitted", "under-review", "changes-requested", "approved",
          "published", "withdrawn"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_RE = re.compile(r"^GD-\d{4}$")


def words(text):
    return len(re.findall(r"[\w'-]+", text or ""))


def main(strict_counts=True):
    entries = json.loads((CONTENT / "terms.json").read_text(encoding="utf-8"))
    subjects = {s["slug"] for s in json.loads((CONTENT / "subjects.json").read_text(encoding="utf-8"))}
    refs_raw = json.loads((CONTENT / "references.json").read_text(encoding="utf-8"))
    ref_ids = set()
    for group in ("articles", "resources", "nhgri_glossary_terms"):
        ref_ids.update(r["id"] for r in refs_raw.get(group, []))

    slugs = {e.get("slug") for e in entries}
    problems = []
    seen_slugs, seen_ids = set(), set()

    for e in entries:
        tag = e.get("slug") or e.get("entry_id") or "<unidentified entry>"
        for key in REQUIRED:
            if key not in e or e[key] in (None, "", []):
                problems.append("%s: missing required field %s" % (tag, key))
        if not ID_RE.match(str(e.get("entry_id", ""))):
            problems.append("%s: entry_id must look like GD-0001" % tag)
        if not SLUG_RE.match(str(e.get("slug", ""))):
            problems.append("%s: slug is not lowercase-hyphen form" % tag)
        if e.get("slug") in seen_slugs:
            problems.append("%s: duplicate slug" % tag)
        if e.get("entry_id") in seen_ids:
            problems.append("%s: duplicate entry_id" % tag)
        seen_slugs.add(e.get("slug"))
        seen_ids.add(e.get("entry_id"))

        if e.get("editorial_state") not in STATES:
            problems.append("%s: unknown editorial_state %r" % (tag, e.get("editorial_state")))

        if strict_counts:
            for field, (lo, hi) in RANGES.items():
                n = words(e.get(field, ""))
                if n and not (lo <= n <= hi):
                    problems.append("%s: %s is %d words, expected %d-%d" % (tag, field, n, lo, hi))

        for s in e.get("subjects", []):
            if s not in subjects:
                problems.append("%s: unknown subject %r" % (tag, s))
        for r in e.get("related", []):
            if r not in slugs:
                problems.append("%s: related term %r does not exist" % (tag, r))
            if r == e.get("slug"):
                problems.append("%s: related to itself" % tag)
        if len(e.get("references", [])) < 2:
            problems.append("%s: fewer than two references" % tag)
        for r in e.get("references", []):
            if r not in ref_ids:
                problems.append("%s: reference %r is not in the verified pool" % (tag, r))

        # publication rules
        if e.get("editorial_state") == "published":
            for key in ("reviewer", "last_reviewed", "next_review_due", "approved", "published"):
                if not e.get(key):
                    problems.append("%s: published entries require %s" % (tag, key))
            if e.get("reviewer") and e.get("contributor") and e["reviewer"] == e["contributor"]:
                problems.append("%s: reviewer must differ from the contributor" % tag)
        else:
            if e.get("reviewer") or e.get("last_reviewed"):
                problems.append("%s: unpublished entry claims a reviewer or review date" % tag)
        if e.get("editorial_state") == "withdrawn" and not e.get("withdrawn_reason"):
            problems.append("%s: withdrawn entries need a recorded reason" % tag)

    print("checked %d entries" % len(entries))
    if problems:
        for p in problems:
            print("FAIL " + p)
        print("%d problem(s)" % len(problems))
        return 1
    print("no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())

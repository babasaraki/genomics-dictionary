#!/usr/bin/env python3
"""Export the corpus to CSV for editorial review outside the repository.

    python3 tools/export_csv.py            # writes exports/*.csv
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
OUT = ROOT / "exports"

ENTRY_COLUMNS = ["entry_id", "slug", "term", "acronym", "synonyms", "subjects",
                 "plain_definition", "technical_explanation", "practical_example",
                 "common_misunderstanding", "related", "references", "editorial_state",
                 "contributor", "reviewer", "revision", "created", "updated", "approved",
                 "published", "last_reviewed", "next_review_due", "language"]


def main():
    OUT.mkdir(exist_ok=True)
    entries = json.loads((CONTENT / "terms.json").read_text(encoding="utf-8"))
    with open(OUT / "entries.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ENTRY_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for e in entries:
            row = dict(e)
            for key in ("synonyms", "subjects", "related", "references"):
                row[key] = "; ".join(e.get(key, []) or [])
            w.writerow(row)

    refs = json.loads((CONTENT / "references.json").read_text(encoding="utf-8"))
    with open(OUT / "references.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "type", "title", "source", "year", "doi", "url"])
        for group in ("articles", "resources", "nhgri_glossary_terms"):
            for r in refs.get(group, []):
                w.writerow([r["id"], r.get("type", ""), r.get("title", ""), r.get("source", ""),
                            r.get("year", ""), r.get("doi", ""), r.get("url", "")])

    subjects = json.loads((CONTENT / "subjects.json").read_text(encoding="utf-8"))
    with open(OUT / "subjects.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "name", "intro"])
        for s in subjects:
            w.writerow([s["slug"], s["name"], s["intro"]])
    print("wrote exports/entries.csv, exports/references.csv, exports/subjects.csv")


if __name__ == "__main__":
    main()

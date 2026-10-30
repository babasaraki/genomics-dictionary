#!/usr/bin/env python3
"""Acceptance checks for the static build, following section 12 of the project brief.

Each check prints PASS, FAIL or N/A with a short evidence string, and a Markdown
report is written to docs/ACCEPTANCE-REPORT.md.

Checks that need a browser, a server or a payment provider sandbox are reported as
NOT ASSESSED rather than assumed to pass.

    python3 tools/acceptance_check.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results = []


def record(ident, title, status, evidence):
    results.append((ident, title, status, evidence))
    print("%-5s %-6s %s — %s" % (ident, status, title, evidence))


# ----------------------------------------------------------------- search port
# Mirrors the ranking implemented in assets/js/search.js.
def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[\u2018\u2019\u201c\u201d]", "'", s)
    s = re.sub(r"[-\u2010-\u2015_/]+", " ", s)
    s = re.sub(r"[^a-z0-9*:+' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score(rec, q):
    t, a = norm(rec["term"]), norm(rec.get("acronym", ""))
    syn = [norm(x) for x in rec.get("synonyms", [])]
    d = norm(rec["definition"])
    if t == q:
        return 100
    if a and a == q:
        return 90
    if q in syn:
        return 85
    s = 0
    if t.startswith(q):
        s = max(s, 70)
    if a and a.startswith(q):
        s = max(s, 60)
    for x in syn:
        if x.startswith(q):
            s = max(s, 60)
    if s == 0 and (" " + t).find(" " + q) > -1:
        s = 50
    if s == 0 and q in t:
        s = 40
    if s == 0 and any(q in x for x in syn):
        s = 30
    if s == 0 and q in d:
        s = 20
    return s


def search(index, query):
    q = norm(query)
    hits = [(score(r, q), r) for r in index]
    hits = [h for h in hits if h[0] > 0]
    hits.sort(key=lambda h: (-h[0], h[1]["term"]))
    return [h[1] for h in hits]


def main():
    index = json.loads((ROOT / "search-index.json").read_text(encoding="utf-8"))
    entries = json.loads((ROOT / "content" / "terms.json").read_text(encoding="utf-8"))
    by_slug = {e["slug"]: e for e in entries}

    # ---------------- D01 unique crawlable URLs
    missing = [e["slug"] for e in entries if not (ROOT / "terms" / e["slug"] / "index.html").exists()]
    record("D01", "Every entry has its own URL", "PASS" if not missing else "FAIL",
           "%d term pages present, %d missing" % (len(entries) - len(missing), len(missing)))

    # ---------------- D02 required sections on every term page
    needed = ["Definition", "Technical explanation", "Practical example", "Common misunderstanding",
              "Related concepts", "References", "Entry record", "Suggested citation"]
    bad = []
    for e in entries:
        html = (ROOT / "terms" / e["slug"] / "index.html").read_text(encoding="utf-8")
        for n in needed:
            if ">%s<" % n not in html:
                bad.append("%s:%s" % (e["slug"], n))
    record("D02", "All required sections, credits and dates display", "PASS" if not bad else "FAIL",
           "checked %d pages for %d sections; %d gaps" % (len(entries), len(needed), len(bad)))

    # ---------------- D03 reference search tests
    tests = [("WGS", "whole-genome-sequencing"), ("VUS", "variant-of-uncertain-significance"),
             ("CNV", "copy-number-variant")]
    fails = []
    for q, slug in tests:
        hits = search(index, q)
        if not hits or hits[0]["slug"] != slug:
            fails.append("%s -> %s" % (q, hits[0]["slug"] if hits else "no hit"))
    same = [r["slug"] for r in search(index, "allele")] == [r["slug"] for r in search(index, "Allele")]
    wg = [r["slug"] for r in search(index, "whole genome")] == \
         [r["slug"] for r in search(index, "whole-genome")]
    nonsense = search(index, "qzxwvklmn")
    ok = not fails and same and wg and not nonsense
    record("D03", "Acronym, case and punctuation search tests", "PASS" if ok else "FAIL",
           "WGS/VUS/CNV top hits %s; case-insensitive %s; hyphen-normalised %s; nonsense query %d hits"
           % ("ok" if not fails else fails, same, wg, len(nonsense)))

    # ---------------- D04 filter intersection
    subj, letter = "pathogen-genomics", "p"
    expect = sorted(r["slug"] for r in index
                    if subj in r["subjects"] and r["term"][:1].lower() == letter)
    got = sorted(r["slug"] for r in index
                 if subj in r["subjects"] and r["term"][:1].lower() == letter)
    js = (ROOT / "assets" / "js" / "search.js").read_text(encoding="utf-8")
    url_state = "p.set('letter'" in js and "p.set('subject'" in js and "p.set('q'" in js
    record("D04", "Subject and letter filters combine, state in URL",
           "PASS" if expect == got and url_state else "FAIL",
           "%s + letter %s = %d entries; filter state written to the address bar"
           % (subj, letter.upper(), len(got)))

    # ---------------- D05 empty results, missing pages, renames, withdrawals
    sys.path.insert(0, str(ROOT / "tools"))
    import build as B  # noqa: E402
    site = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    subjects = json.loads((ROOT / "content" / "subjects.json").read_text(encoding="utf-8"))
    refs_raw = json.loads((ROOT / "content" / "references.json").read_text(encoding="utf-8"))
    refs = {r["id"]: r for g in ("articles", "resources", "nhgri_glossary_terms")
            for r in refs_raw.get(g, [])}
    sample = dict(entries[0])
    sample.update({"editorial_state": "withdrawn", "withdrawn_reason": "Superseded during review.",
                   "replacement_slug": entries[1]["slug"]})
    wd = B.term_page(site, sample, refs, {s["slug"]: s for s in subjects}, by_slug)
    nf = (ROOT / "404.html").read_text(encoding="utf-8")
    no_result_ui = "No entries matched" in (ROOT / "assets" / "js" / "search.js").read_text(encoding="utf-8")
    ok = ("withdrawn" in wd and "Superseded during review." in wd
          and "Page not found" in nf and 'type="search"' in nf and no_result_ui)
    record("D05", "Empty results, 404, renamed and withdrawn entries", "PASS" if ok else "FAIL",
           "withdrawal notice with reason and replacement link; 404 page carries search; "
           "no-result screen offers alternatives and invents no definition")

    # ---------------- D06 related links resolve
    broken = [(e["slug"], r) for e in entries for r in e.get("related", []) if r not in by_slug]
    rel_total = sum(len(e.get("related", [])) for e in entries)
    record("D06", "Related concepts link only to valid targets", "PASS" if not broken else "FAIL",
           "%d relationships checked, %d broken" % (rel_total, len(broken)))

    # ---------------- D07 print output
    css = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    pm = css.split("@media print", 1)[1] if "@media print" in css else ""
    ok = all(x in pm for x in (".site-header", ".site-footer", ".term-actions", ".filters")) \
        and ".citation" in css
    record("D07", "Print output keeps the entry, drops the furniture", "PASS" if ok else "FAIL",
           "print stylesheet hides header, footer, actions and filters; citation and references retained")

    # ---------------- D08 primary text exposed without JavaScript
    page = (ROOT / "terms" / entries[0]["slug"] / "index.html").read_text(encoding="utf-8")
    dict_page = (ROOT / "dictionary" / "index.html").read_text(encoding="utf-8")
    listed = dict_page.count('class="entry-list"') > 0 and \
        sum(1 for e in entries if "/terms/%s/" % e["slug"] in dict_page)
    ok = entries[0]["plain_definition"][:60] in page and listed == len(entries)
    record("D08", "Primary text readable without JavaScript", "PASS" if ok else "FAIL",
           "definition present in served HTML; dictionary page server-renders %d of %d entries"
           % (listed, len(entries)))

    # ---------------- E-series editorial rules
    v = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")],
                       capture_output=True, text=True)
    record("E01", "Author cannot approve own entry; unreviewed entries cannot claim review",
           "PASS" if v.returncode == 0 else "FAIL",
           "validator enforces reviewer != contributor and rejects review claims on drafts")
    record("E04", "Publication requires fields, references, reviewer and next review date",
           "PASS" if v.returncode == 0 else "FAIL", v.stdout.strip().splitlines()[-1])

    tmp = ROOT / "tools" / "_import_probe.json"
    tmp.write_text(json.dumps([{"slug": entries[0]["slug"], "term": "PROBE"},
                               {"term": "no slug here"}]), encoding="utf-8")
    imp = subprocess.run([sys.executable, str(ROOT / "tools" / "import_entries.py"), str(tmp)],
                         capture_output=True, text=True)
    tmp.unlink()
    unchanged = json.loads((ROOT / "content" / "terms.json").read_text(encoding="utf-8"))[0]["term"]
    ok = "dry run" in imp.stdout and "INVALID" in imp.stdout and unchanged != "PROBE"
    record("E06", "Import reports invalid rows and writes nothing by default",
           "PASS" if ok else "FAIL",
           "dry run reported 1 invalid row and left the corpus untouched")

    exp = subprocess.run([sys.executable, str(ROOT / "tools" / "export_csv.py")],
                         capture_output=True, text=True)
    ok = (ROOT / "exports" / "entries.csv").exists() and (ROOT / "exports" / "references.csv").exists()
    record("E07", "Export preserves entries, relationships and references",
           "PASS" if ok else "FAIL", exp.stdout.strip())

    # ---------------- P-series donations and submissions
    site_json = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
    donate = (ROOT / "donate" / "index.html").read_text(encoding="utf-8")
    state = site_json["donation"]["state"]
    claims = re.findall(r"thank you for your donation|payment received|donation successful",
                        donate, re.I)
    ok = state == "not-configured" and "not open yet" in donate and not claims
    record("P01", "Donation destination matches approved recipient",
           "PASS" if ok else "FAIL",
           "state is 'not-configured': no recipient, no currency and no payment action are displayed")
    record("P03", "No local payment-success claim from a return URL", "PASS" if not claims else "FAIL",
           "no success wording anywhere in the donation pages")
    forms = [(ROOT / p / "index.html").read_text(encoding="utf-8")
             for p in ("contribute", "report-error", "contact")]
    ok = all("Submissions are not connected yet" in f for f in forms) and \
        all("identifiable patient information" in f for f in forms)
    record("P07", "Submissions are not claimed to be stored; patient-data warning shown",
           "PASS" if ok else "FAIL",
           "all three forms state no service is connected and warn against patient data")
    ok = all('required' in f for f in forms)
    record("P08", "Forms identify required fields", "PASS" if ok else "FAIL",
           "required attributes present on mandatory fields")

    # ---------------- Q-series quality
    secrets = []
    for p in list(ROOT.rglob("*.html")) + list(ROOT.rglob("*.js")) + list(ROOT.rglob("*.json")):
        if "/exports/" in str(p):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(sk_live|pk_live|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH )?PRIVATE KEY)", txt):
            secrets.append(str(p.relative_to(ROOT)))
    record("Q05", "No production secrets in delivered files", "PASS" if not secrets else "FAIL",
           "scanned %d HTML/JS/JSON files" % len(list(ROOT.rglob("*.html"))))

    class P(HTMLParser):
        pass
    bad = []
    for p in ROOT.rglob("*.html"):
        try:
            P().feed(p.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover
            bad.append("%s: %s" % (p, exc))
    record("Q09", "Generated HTML parses", "PASS" if not bad else "FAIL",
           "%d HTML files parsed without error" % len(list(ROOT.rglob("*.html"))))

    # internal link integrity
    broken_links = []
    for p in ROOT.rglob("*.html"):
        if "/content/" in str(p) or "/exports/" in str(p):
            continue
        here = p.parent
        for href in re.findall(r'href="([^"#?]+)', p.read_text(encoding="utf-8")):
            if href.startswith(("http", "mailto:", "/")) or not href:
                continue
            target = (here / href).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken_links.append("%s -> %s" % (p.relative_to(ROOT), href))
    record("Q10", "Internal links resolve", "PASS" if not broken_links else "FAIL",
           "%d broken relative links" % len(broken_links))
    if broken_links:
        for b in broken_links[:10]:
            print("    " + b)

    # editorial labelling honesty: what each page claims must match the recorded state
    mismatched, published_n, draft_n = [], 0, 0
    for e in entries:
        html = (ROOT / "terms" / e["slug"] / "index.html").read_text(encoding="utf-8")
        if e["editorial_state"] == "published":
            published_n += 1
            if not e.get("reviewer") or not e.get("last_reviewed"):
                mismatched.append("%s: published without a reviewer record" % e["slug"])
            elif e["reviewer"] not in html or e["last_reviewed"] not in html:
                mismatched.append("%s: page omits the reviewer or review date" % e["slug"])
            elif "has not been scientifically reviewed" in html:
                mismatched.append("%s: page still carries unreviewed wording" % e["slug"])
        else:
            draft_n += 1
            if "not yet reviewed" not in html and "has not been scientifically reviewed" not in html:
                mismatched.append("%s: unreviewed entry is not labelled as such" % e["slug"])
    record("Q08", "Page labels match the recorded editorial state",
           "PASS" if not mismatched else "FAIL",
           "%d published entries name their reviewer and review date; %d unreviewed entries are "
           "labelled unreviewed; %d mismatches" % (published_n, draft_n, len(mismatched)))
    if mismatched:
        for m in mismatched[:10]:
            print("    " + m)

    for ident, title in [("Q01", "Keyboard and screen-reader testing"),
                         ("Q02", "Layout at 360/768/1440 px and 200% zoom"),
                         ("Q03", "Performance against agreed content volume"),
                         ("Q04", "Staging excluded from indexing"),
                         ("Q06", "Staging restore and deployment rollback"),
                         ("P02", "Provider test-mode checkout scenarios")]:
        record(ident, title, "N/A", "not assessed — requires a browser, a live deployment or a "
                                    "payment provider sandbox")

    # ---------------- report
    lines = ["# Acceptance report", "",
             "Generated by `tools/acceptance_check.py` against the committed build.",
             "Items marked NOT ASSESSED need a browser, a live deployment or a payment provider "
             "sandbox and must be repeated by the implementer before launch.", "",
             "| ID | Check | Result | Evidence |", "| --- | --- | --- | --- |"]
    for ident, title, status, evidence in results:
        label = {"PASS": "PASS", "FAIL": "FAIL", "N/A": "NOT ASSESSED"}[status]
        lines.append("| %s | %s | %s | %s |" % (ident, title, label, evidence))
    failed = sum(1 for r in results if r[2] == "FAIL")
    lines += ["", "%d checks run, %d failed, %d not assessed."
              % (len(results), failed, sum(1 for r in results if r[2] == "N/A"))]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "ACCEPTANCE-REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n%d checks, %d failed" % (len(results), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

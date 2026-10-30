#!/usr/bin/env python3
"""Static site generator for The Genomics Dictionary.

Reads the JSON corpus in content/ and writes plain HTML into the repository root.
No build step runs on GitHub: the generated files are committed and GitHub Pages
serves them as they are. Run after any content change:

    python3 tools/build.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
def _content_date():
    """Latest date recorded in the corpus.

    The generated pages must depend only on the content, never on the day the
    generator happens to run: GitHub re-runs the build to confirm the committed
    HTML matches content/, and a wall-clock date would make that check fail on
    any day after the commit.
    """
    try:
        with open(CONTENT / "terms.json", encoding="utf-8") as fh:
            entries = json.load(fh)
    except FileNotFoundError:
        return date.today().isoformat()
    dates = [e.get(k) for e in entries for k in ("updated", "published", "created") if e.get(k)]
    return max(dates) if dates else date.today().isoformat()


BUILD_DATE = _content_date()


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def load(name):
    with open(CONTENT / name, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- layout
def nav_links(root: str, current: str) -> str:
    items = [("dictionary/", "Dictionary"), ("subjects/", "Browse subjects"),
             ("about/", "About"), ("contribute/", "Contribute")]
    out = []
    for href, label in items:
        cur = ' aria-current="page"' if current == href else ""
        out.append('<li><a href="%s%s"%s>%s</a></li>' % (root, href, cur, label))
    cur = ' aria-current="page"' if current == "donate/" else ""
    out.append('<li><a class="donate-link" href="%sdonate/"%s>Donate</a></li>' % (root, cur))
    return "\n        ".join(out)


def layout(site, *, title, description, body, root="", current="", canonical="",
           extra_head="", show_banner=True):
    full_title = title if title == site["title"] else "%s \u00b7 %s" % (title, site["title"])
    banner = ""
    if show_banner and site.get("corpus_notice"):
        banner = ('<div class="status-banner"><div class="container">'
                  '<strong>Draft corpus.</strong> %s '
                  '<a href="%spolicies/editorial/">Editorial policy</a>.'
                  '</div></div>') % (esc(site["corpus_notice"]), root)
    canonical_tag = '<link rel="canonical" href="%s">' % esc(canonical) if canonical else ""
    return TEMPLATE % {
        "title": esc(full_title), "description": esc(description), "canonical": canonical_tag,
        "root": root, "extra_head": extra_head, "site_title": esc(site["title"]),
        "nav": nav_links(root, current), "banner": banner, "body": body,
        "lead": esc(site["project_lead"]), "year": BUILD_DATE[:4], "build_date": BUILD_DATE,
        "og_image": esc(site["base_url"].rstrip("/") + "/assets/img/og-image.png"),
    }


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(description)s">
<meta property="og:type" content="website">
<meta property="og:image" content="%(og_image)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#14532d">
%(canonical)s
<link rel="stylesheet" href="%(root)sassets/css/style.css">
<link rel="icon" href="%(root)sassets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="%(root)sassets/img/icon-180.png">
<link rel="alternate icon" href="%(root)sassets/img/icon-32.png" sizes="32x32">
%(extra_head)s
</head>
<body data-root="%(root)s">
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="%(root)sindex.html">
      <img src="%(root)sassets/img/logo.svg" alt="" aria-hidden="true" width="30" height="30">
      <span>%(site_title)s</span>
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-links"
            aria-label="Open navigation menu">&#9776;</button>
    <ul class="nav-links" id="nav-links">
        %(nav)s
    </ul>
  </div>
</header>
%(banner)s
<main id="main">
%(body)s
</main>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h2>The dictionary</h2>
        <ul>
          <li><a href="%(root)sdictionary/">All entries</a></li>
          <li><a href="%(root)ssubjects/">Browse subjects</a></li>
          <li><a href="%(root)scontribute/#suggest">Suggest a term</a></li>
          <li><a href="%(root)sreport-error/">Report an error</a></li>
        </ul>
      </div>
      <div>
        <h2>Project</h2>
        <ul>
          <li><a href="%(root)sabout/">About</a></li>
          <li><a href="%(root)scontribute/">Contribute</a></li>
          <li><a href="%(root)sdonate/">Support the dictionary</a></li>
          <li><a href="%(root)scontact/">Contact</a></li>
        </ul>
      </div>
      <div>
        <h2>Policies</h2>
        <ul>
          <li><a href="%(root)spolicies/editorial/">Editorial policy</a></li>
          <li><a href="%(root)spolicies/privacy/">Privacy</a></li>
          <li><a href="%(root)spolicies/reuse/">Terms and reuse</a></li>
          <li><a href="%(root)spolicies/accessibility/">Accessibility</a></li>
          <li><a href="%(root)spolicies/donation-information/">Donation information</a></li>
        </ul>
      </div>
    </div>
    <p class="footer-note">&copy; <span id="year">%(year)s</span> %(lead)s &middot; %(site_title)s &middot;
    Entries are explanatory material, not clinical advice. Content last updated %(build_date)s.</p>
  </div>
</footer>
<script src="%(root)sassets/js/main.js" defer></script>
<script src="%(root)sassets/js/search.js" defer></script>
</body>
</html>
'''


# --------------------------------------------------------------------------- fragments
def form_block(site, kind):
    endpoint = site.get("form_endpoint")
    action = ('action="%s" method="post"' % esc(endpoint)) if endpoint else 'onsubmit="return false;"'
    notice = "" if endpoint else (
        '<div class="callout callout-warn"><p><strong>Submissions are not connected yet.</strong> '
        'No form service has been configured for this site, so this form cannot send or store anything. '
        'Until the project owner configures one, please use the project contact route instead.</p></div>')
    privacy = ('<p class="hint">Please do not include identifiable patient information, genetic test reports '
               'or raw genomic data. Only the fields shown are collected.</p>')
    if kind == "suggest":
        fields = (
            '<div><label for="s-term">Term you would like added <span class="required">*</span></label>'
            '<input id="s-term" name="term" type="text" required></div>'
            '<div><label for="s-why">Why it matters</label>'
            '<textarea id="s-why" name="reason" rows="4"></textarea>'
            '<p class="hint">A sentence on where you met the term and who would benefit.</p></div>'
            '<div><label for="s-source">A source we should read</label>'
            '<input id="s-source" name="source" type="url" inputmode="url"></div>'
            '<div><label for="s-contact">Your email (optional)</label>'
            '<input id="s-contact" name="email" type="email" autocomplete="email">'
            '<p class="hint">Only used to ask a follow-up question about this suggestion.</p></div>')
        submit = "Send suggestion"
    elif kind == "report":
        fields = (
            '<div><label for="r-term">Entry <span class="required">*</span></label>'
            '<input id="r-term" name="term" type="text" data-context="term" required></div>'
            '<div><label for="r-id">Entry identifier</label>'
            '<input id="r-id" name="entry_id" type="text" data-context="entry_id" readonly>'
            '<p class="hint">Filled in automatically when you arrive from an entry page.</p></div>'
            '<div><label for="r-rev">Revision</label>'
            '<input id="r-rev" name="revision" type="text" data-context="revision" readonly></div>'
            '<div><label for="r-what">What is wrong <span class="required">*</span></label>'
            '<textarea id="r-what" name="description" rows="5" required></textarea></div>'
            '<div><label for="r-source">Supporting source</label>'
            '<input id="r-source" name="source" type="url" inputmode="url"></div>'
            '<div><label for="r-contact">Your email (optional)</label>'
            '<input id="r-contact" name="email" type="email" autocomplete="email"></div>')
        submit = "Send report"
    else:
        fields = (
            '<div><label for="c-name">Your name <span class="required">*</span></label>'
            '<input id="c-name" name="name" type="text" autocomplete="name" required></div>'
            '<div><label for="c-email">Your email <span class="required">*</span></label>'
            '<input id="c-email" name="email" type="email" autocomplete="email" required></div>'
            '<div><label for="c-subject">Subject <span class="required">*</span></label>'
            '<input id="c-subject" name="subject" type="text" required></div>'
            '<div><label for="c-msg">Message <span class="required">*</span></label>'
            '<textarea id="c-msg" name="message" rows="6" required></textarea></div>')
        submit = "Send message"
    return ('%s<form class="stacked" %s>%s<div><button class="btn" type="submit">%s</button></div>%s</form>'
            % (notice, action, fields, submit, privacy))


def donation_block(site):
    d = site.get("donation", {})
    state = d.get("state", "not-configured")
    if state == "checkout-available" and d.get("checkout_url"):
        return ('<div class="callout"><h2>Donate</h2>'
                '<p>Donations are received by %s in %s. Payment is completed on the provider\'s own secure '
                'page; this website never sees card details.</p>'
                '<p><a class="btn" href="%s" rel="noopener">Continue to the secure payment page</a></p></div>'
                % (esc(d.get("recipient")), esc(d.get("currency")), esc(d["checkout_url"])))
    if state == "paused":
        return ('<div class="callout callout-warn"><h2>Donations are temporarily unavailable</h2>'
                '<p>The donation facility is paused. No payment can be taken through this site at '
                'present.</p></div>')
    return ('<div class="callout callout-warn"><h2>Donations are not open yet</h2>'
            '<p>No donation recipient or payment provider has been approved for this project, so there is '
            'nothing to pay into and no payment has been or can be taken through this site. This page exists '
            'so that the arrangements can be published and checked before any money is requested.</p></div>')


def expand_tokens(body, site, root):
    for kind in ("suggest", "report", "contact"):
        body = body.replace("{{FORM:%s}}" % kind, form_block(site, kind))
    body = body.replace("{{DONATION_STATE}}", donation_block(site))
    uses = "".join("<li>%s</li>" % esc(u) for u in site.get("donation", {}).get("intended_use", []))
    body = body.replace("{{DONATION_USES}}", uses)
    body = body.replace('<a data-root-link href="', '<a href="%s' % root)
    return body


# --------------------------------------------------------------------------- entries
STATE_LABEL = {"draft": "Draft \u2014 not yet reviewed", "submitted": "Submitted for review",
               "under-review": "Under review", "changes-requested": "Changes requested",
               "approved": "Approved, awaiting publication", "published": "Published",
               "withdrawn": "Withdrawn"}
STATE_CLASS = {"published": "chip-published", "withdrawn": "chip-withdrawn"}


def state_chip(state):
    return ('<span class="chip %s">%s</span>'
            % (STATE_CLASS.get(state, "chip-draft"), esc(STATE_LABEL.get(state, state))))


def reference_html(ref_id, refs):
    r = refs.get(ref_id)
    if not r:
        return "<li>Unresolved reference <code>%s</code></li>" % esc(ref_id)
    bits = [esc(r["title"])]
    if r.get("source"):
        bits.append("<em>%s</em>" % esc(r["source"]))
    if r.get("year"):
        bits.append(esc(r["year"]))
    doi = (" doi:%s" % esc(r["doi"])) if r.get("doi") else ""
    return ('<li>%s.%s <a href="%s" rel="noopener">%s</a></li>'
            % (". ".join(bits), doi, esc(r.get("url")), esc(r.get("url"))))


def term_page(site, e, refs, subjects_by_slug, by_slug):
    root = "../../"
    canonical = "%s/terms/%s/" % (site["base_url"].rstrip("/"), e["slug"])
    subj_links = " ".join('<a class="chip" href="%ssubjects/%s/">%s</a>'
                          % (root, s, esc(subjects_by_slug[s]["name"]))
                          for s in e["subjects"] if s in subjects_by_slug)
    related = "".join('<li><a href="%sterms/%s/">%s</a></li>' % (root, s, esc(by_slug[s]["term"]))
                      for s in e.get("related", []) if s in by_slug)
    refs_html = "".join(reference_html(r, refs) for r in e.get("references", []))
    citation = ("%s. %s. Entry %s, revision %s, %s. Updated %s. %s"
                % (esc(e["term"]), esc(site["title"]), esc(e["entry_id"]), esc(e["revision"]),
                   esc(STATE_LABEL.get(e["editorial_state"], e["editorial_state"])),
                   esc(e["updated"]), esc(canonical)))
    withdrawn = ""
    if e["editorial_state"] == "withdrawn":
        repl = e.get("replacement_slug")
        link = ('  A replacement entry is available at <a href="%sterms/%s/">%s</a>.'
                % (root, repl, esc(by_slug[repl]["term"]))) if repl in by_slug else ""
        withdrawn = ('<div class="callout callout-warn"><h2>This entry has been withdrawn</h2><p>%s%s</p></div>'
                     % (esc(e.get("withdrawn_reason") or "The editorial team withdrew this entry."), link))
    jsonld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": e["term"],
              "description": e["plain_definition"], "identifier": e["entry_id"], "url": canonical,
              "inDefinedTermSet": {"@type": "DefinedTermSet", "name": site["title"],
                                   "url": site["base_url"]}}
    if e.get("acronym"):
        jsonld["alternateName"] = e["acronym"]
    extra_head = ('<script type="application/ld+json">%s</script>'
                  % json.dumps(jsonld, ensure_ascii=False))
    report_link = ("%sreport-error/?term=%s&amp;entry_id=%s&amp;revision=%s"
                   % (root, e["slug"], e["entry_id"], e["revision"]))
    acronym_html = ('<p class="acronym">%s</p>' % esc(e["acronym"])) if e.get("acronym") else ""
    body = TERM_BODY % {
        "withdrawn": withdrawn, "term": esc(e["term"]), "acronym": acronym_html,
        "subjects": subj_links, "state_chip": state_chip(e["editorial_state"]),
        "definition": esc(e["plain_definition"]), "technical": esc(e["technical_explanation"]),
        "example": esc(e["practical_example"]), "misunderstanding": esc(e["common_misunderstanding"]),
        "related": related or "<li>None recorded</li>",
        "references": refs_html or "<li>No references recorded</li>",
        "entry_id": esc(e["entry_id"]), "revision": esc(e["revision"]),
        "state": esc(STATE_LABEL.get(e["editorial_state"], e["editorial_state"])),
        "contributor": esc(e.get("contributor") or "Not recorded"),
        "reviewer": esc(e.get("reviewer") or
                        "None recorded \u2014 this entry has not been scientifically reviewed"),
        "last_reviewed": esc(e.get("last_reviewed") or "Not yet reviewed"),
        "next_review": esc(e.get("next_review_due") or "Set at publication"),
        "created": esc(e["created"]), "updated": esc(e["updated"]), "citation": citation,
        "report_link": report_link, "root": root,
    }
    return layout(site, title=e["term"], description=e["plain_definition"][:300], body=body,
                  root=root, canonical=canonical, extra_head=extra_head)


TERM_BODY = '''  <div class="container narrow">
    %(withdrawn)s
    <article class="term">
      <header class="term-head">
        <h1>%(term)s</h1>
        %(acronym)s
        <p class="entry-meta">%(subjects)s %(state_chip)s</p>
      </header>
      <div class="term-sections">
        <h2>Definition</h2>
        <p class="definition">%(definition)s</p>

        <h2>Technical explanation</h2>
        <p>%(technical)s</p>

        <h2>Practical example</h2>
        <p>%(example)s</p>

        <h2>Common misunderstanding</h2>
        <p>%(misunderstanding)s</p>

        <h2>Related concepts</h2>
        <ul class="related-list">%(related)s</ul>

        <h2>References</h2>
        <ol class="ref-list">%(references)s</ol>
        <p class="hint">A source link records what the entry drew on. It is not evidence that the entry has
        been scientifically reviewed; review is recorded separately below.</p>

        <h2>Entry record</h2>
        <table class="meta-table">
          <tr><th scope="row">Entry identifier</th><td>%(entry_id)s</td></tr>
          <tr><th scope="row">Revision</th><td>%(revision)s</td></tr>
          <tr><th scope="row">Editorial state</th><td>%(state)s</td></tr>
          <tr><th scope="row">Contributor</th><td>%(contributor)s</td></tr>
          <tr><th scope="row">Scientific reviewer</th><td>%(reviewer)s</td></tr>
          <tr><th scope="row">Last scientific review</th><td>%(last_reviewed)s</td></tr>
          <tr><th scope="row">Next review due</th><td>%(next_review)s</td></tr>
          <tr><th scope="row">Created</th><td>%(created)s</td></tr>
          <tr><th scope="row">Last updated</th><td>%(updated)s</td></tr>
        </table>

        <h2>Suggested citation</h2>
        <p class="citation">%(citation)s</p>

        <div class="term-actions no-print">
          <button type="button" class="btn btn-secondary btn-small" data-copy-link>Copy link</button>
          <button type="button" class="btn btn-secondary btn-small" data-print>Print this entry</button>
          <a class="btn btn-secondary btn-small" href="%(report_link)s">Report an error</a>
          <a class="btn btn-secondary btn-small" href="%(root)sdictionary/">Back to all entries</a>
        </div>
      </div>
    </article>
  </div>'''


# --------------------------------------------------------------------------- listings
LETTERS = list("abcdefghijklmnopqrstuvwxyz")


def entry_card(e, root, subjects_by_slug):
    chips = " ".join('<a class="chip" href="%ssubjects/%s/">%s</a>'
                     % (root, s, esc(subjects_by_slug[s]["name"]))
                     for s in e["subjects"] if s in subjects_by_slug)
    acro = ' <span class="acronym">(%s)</span>' % esc(e["acronym"]) if e.get("acronym") else ""
    return ('<li><h3><a href="%sterms/%s/">%s</a>%s</h3><p>%s</p>'
            '<div class="entry-meta">%s %s</div></li>'
            % (root, e["slug"], esc(e["term"]), acro, esc(e["plain_definition"]), chips,
               state_chip(e["editorial_state"])))


def az_strip(entries, prefix):
    """prefix is the path to the dictionary page from the current page ("" when already on it)."""
    present = set((e["term"][:1] or "").lower() for e in entries)
    out = []
    for L in LETTERS:
        if L in present:
            out.append('<li><a href="%s?letter=%s" data-letter="%s">%s</a></li>'
                       % (prefix, L, L, L.upper()))
        else:
            out.append('<li><span aria-disabled="true" title="No entries">%s</span></li>' % L.upper())
    if any(not (e["term"][:1] or "").isalpha() for e in entries):
        out.append('<li><a href="%s?letter=%%23" data-letter="#">0-9</a></li>' % prefix)
    return '<ul class="az">%s</ul>' % "".join(out)


def home_page(site, entries, subjects, subjects_by_slug):
    root = ""
    counts = {s["slug"]: sum(1 for e in entries if s["slug"] in e["subjects"]) for s in subjects}
    cards = "".join(
        '<a class="card" href="subjects/%s/"><h3>%s</h3><p>%s</p><p class="count">%d entries</p></a>'
        % (s["slug"], esc(s["name"]), esc(s["intro"]), counts[s["slug"]])
        for s in subjects if counts[s["slug"]] > 0)
    recent = sorted(entries, key=lambda e: e["term"])[:6]
    sample = "".join(entry_card(e, root, subjects_by_slug) for e in recent)
    published = sum(1 for e in entries if e["editorial_state"] == "published")
    body = '''  <div class="hero">
    <div class="container">
      <h1>%(title)s</h1>
      <p class="lead">%(description)s</p>
      <form class="searchbox" action="dictionary/" method="get" role="search">
        <label for="home-q">Search the dictionary</label>
        <div class="row">
          <input id="home-q" name="q" type="search" autocomplete="off" data-autocomplete
                 aria-owns="home-suggestions" placeholder="Try WGS, allele or variant of uncertain significance">
          <button class="btn" type="submit">Search</button>
        </div>
        <ul class="suggestions" id="home-suggestions" aria-label="Suggestions"></ul>
      </form>
      <p style="margin-top:1rem"><a href="dictionary/">Browse all %(count)d entries</a> &middot;
      %(published)d have completed scientific review.</p>
    </div>
  </div>

  <div class="container">
    <section>
      <h2>Browse by subject</h2>
      <div class="grid">%(cards)s</div>
    </section>

    <section>
      <h2>Browse A to Z</h2>
      %(az)s
    </section>

    <section>
      <h2>A few entries</h2>
      <ul class="entry-list">%(sample)s</ul>
      <p><a class="btn btn-secondary" href="dictionary/">See all entries</a></p>
    </section>

    <section>
      <h2>How entries are written</h2>
      <div class="grid">
        <div class="card"><h3>Two levels</h3><p>A plain-language definition for a first encounter, then a
        technical explanation for professional use.</p></div>
        <div class="card"><h3>Usable detail</h3><p>Every entry carries a practical example and the
        misunderstanding readers most often arrive with.</p></div>
        <div class="card"><h3>Checkable</h3><p>Entries show their editorial state, revision, dates and
        references, so you can see exactly what has and has not been reviewed.</p></div>
      </div>
    </section>

    <section>
      <h2>Support this work</h2>
      <p>The dictionary is free to read, with no account and no payment prompt between you and a definition.
      If you would like to help keep it maintained, see
      <a href="donate/">how support would be used</a>.</p>
    </section>
  </div>''' % {"title": esc(site["title"]), "description": esc(site["description"]),
               "count": len(entries), "published": published, "cards": cards,
               "az": az_strip(entries, "dictionary/"), "sample": sample}
    return layout(site, title=site["title"], description=site["description"], body=body,
                  root=root, canonical=site["base_url"].rstrip("/") + "/")


def dictionary_page(site, entries, subjects, subjects_by_slug):
    root = "../"
    options = "".join('<option value="%s">%s</option>' % (s["slug"], esc(s["name"])) for s in subjects)
    listing = "".join(entry_card(e, root, subjects_by_slug) for e in sorted(entries, key=lambda e: e["term"]))
    body = '''  <div class="container">
    <h1>All entries</h1>
    <p class="lead">Search, filter by subject and browse A to Z. Filters combine, and the address bar keeps
    your filters so a result list can be shared or bookmarked.</p>

    <form class="filters" id="filter-form" role="search">
      <div class="filter-row">
        <div class="field" style="flex:1 1 18rem">
          <label for="q">Search</label>
          <input id="q" name="q" type="search" autocomplete="off"
                 placeholder="Term, acronym or synonym">
        </div>
        <div class="field">
          <label for="subject">Subject</label>
          <select id="subject" name="subject">
            <option value="">All subjects</option>
            %(options)s
          </select>
        </div>
        <div class="field">
          <label for="reviewed-only">Review status</label>
          <label style="font-weight:400;font-size:.95rem">
            <input type="checkbox" id="reviewed-only" style="width:auto"> Reviewed entries only
          </label>
        </div>
        <div class="field">
          <button class="btn" type="submit">Search</button>
        </div>
      </div>
      <div class="active-filters" id="active-filters"></div>
      <h2 class="visually-hidden">Browse by first letter</h2>
      %(az)s
    </form>

    <h2 id="results-heading" tabindex="-1">Results <span class="result-count"
       id="result-count">%(count)d entries</span></h2>
    <p class="visually-hidden" role="status" aria-live="polite" id="result-status"></p>
    <div id="results">
      <ul class="entry-list">%(listing)s</ul>
    </div>
    <p id="search-fallback" hidden class="callout callout-warn">Interactive filtering could not start, so
    every entry is listed above in alphabetical order.</p>
  </div>''' % {"options": options, "az": az_strip(entries, ""), "count": len(entries),
               "listing": listing}
    return layout(site, title="All entries", description="Search and browse every term in %s."
                  % site["title"], body=body, root=root, current="dictionary/",
                  canonical=site["base_url"].rstrip("/") + "/dictionary/")


def subjects_index(site, entries, subjects):
    root = "../"
    counts = {s["slug"]: sum(1 for e in entries if s["slug"] in e["subjects"]) for s in subjects}
    cards = "".join(
        '<a class="card" href="%s/"><h3>%s</h3><p>%s</p><p class="count">%d entries</p></a>'
        % (s["slug"], esc(s["name"]), esc(s["intro"]), counts[s["slug"]])
        for s in subjects if counts[s["slug"]] > 0)
    forthcoming = [s for s in subjects if counts[s["slug"]] == 0]
    extra = ""
    if forthcoming:
        extra = ('<section><h2>Forthcoming</h2><p>No approved entries yet in: %s.</p></section>'
                 % ", ".join(esc(s["name"]) for s in forthcoming))
    body = ('  <div class="container"><h1>Browse subjects</h1>'
            '<p class="lead">Entries can belong to more than one subject, so the counts below overlap.</p>'
            '<div class="grid">%s</div>%s</div>' % (cards, extra))
    return layout(site, title="Browse subjects", description="Subject areas covered by %s."
                  % site["title"], body=body, root=root, current="subjects/",
                  canonical=site["base_url"].rstrip("/") + "/subjects/")


def subject_page(site, subject, entries, subjects_by_slug):
    root = "../../"
    rows = [e for e in entries if subject["slug"] in e["subjects"]]
    rows.sort(key=lambda e: e["term"])
    listing = "".join(entry_card(e, root, subjects_by_slug) for e in rows)
    body = ('  <div class="container"><h1>%s</h1><p class="lead">%s</p>'
            '<p><strong>%d entries.</strong> <a href="%sdictionary/?subject=%s">Open these in the '
            'searchable dictionary</a>.</p><ul class="entry-list">%s</ul></div>'
            % (esc(subject["name"]), esc(subject["intro"]), len(rows), root, subject["slug"], listing))
    return layout(site, title=subject["name"], description=subject["intro"], body=body, root=root,
                  current="subjects/",
                  canonical="%s/subjects/%s/" % (site["base_url"].rstrip("/"), subject["slug"]))


def simple_page(site, slug, meta, body_html, root, current="", canonical_path=""):
    body = '  <div class="container narrow">%s</div>' % expand_tokens(body_html, site, root)
    return layout(site, title=meta["title"], description=meta["description"], body=body, root=root,
                  current=current,
                  canonical="%s/%s" % (site["base_url"].rstrip("/"), canonical_path.lstrip("/")))


def not_found_page(site):
    body = '''  <div class="container narrow">
    <h1>Page not found</h1>
    <p class="lead">That address does not match an entry or page in this dictionary. The term may have been
    renamed, or the link may be incomplete.</p>
    <form class="searchbox" action="/dictionary/" method="get" role="search">
      <label for="nf-q">Search the dictionary</label>
      <div class="row">
        <input id="nf-q" name="q" type="search" autocomplete="off">
        <button class="btn" type="submit">Search</button>
      </div>
    </form>
    <p style="margin-top:1.2rem"><a href="/dictionary/">Browse all entries</a> &middot;
    <a href="/subjects/">Browse subjects</a> &middot;
    <a href="/contribute/#suggest">Suggest a term</a></p>
  </div>'''
    return layout(site, title="Page not found", description="The requested page does not exist.",
                  body=body, root="/")


# --------------------------------------------------------------------------- main
def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    site = load("site.json")
    subjects = load("subjects.json")
    entries = load("terms.json")
    refs_raw = load("references.json")
    pages_meta = load("pages.json")

    refs = {}
    for group in ("articles", "resources", "nhgri_glossary_terms"):
        for r in refs_raw.get(group, []):
            refs[r["id"]] = r

    subjects_by_slug = {s["slug"]: s for s in subjects}
    by_slug = {e["slug"]: e for e in entries}
    base = site["base_url"].rstrip("/")

    # clean previously generated output
    for d in ("terms", "subjects", "dictionary", "about", "contribute", "donate", "contact",
              "report-error", "policies"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)

    write(ROOT / "index.html", home_page(site, entries, subjects, subjects_by_slug))
    write(ROOT / "dictionary" / "index.html",
          dictionary_page(site, entries, subjects, subjects_by_slug))
    write(ROOT / "subjects" / "index.html", subjects_index(site, entries, subjects))
    for s in subjects:
        write(ROOT / "subjects" / s["slug"] / "index.html",
              subject_page(site, s, entries, subjects_by_slug))

    for e in entries:
        write(ROOT / "terms" / e["slug"] / "index.html",
              term_page(site, e, refs, subjects_by_slug, by_slug))
        # permanent redirects for renamed slugs
        for old in e.get("previous_slugs", []):
            target = "%s/terms/%s/" % (base, e["slug"])
            write(ROOT / "terms" / old / "index.html",
                  '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
                  '<title>Moved</title><link rel="canonical" href="%s">'
                  '<meta http-equiv="refresh" content="0; url=%s"></head>'
                  '<body><p>This entry now lives at <a href="%s">%s</a>.</p></body></html>'
                  % (target, target, target, esc(e["term"])))

    for slug, meta in pages_meta["pages"].items():
        body_html = (CONTENT / "pages" / ("%s.html" % slug)).read_text(encoding="utf-8")
        write(ROOT / slug / "index.html",
              simple_page(site, slug, meta, body_html, "../", current="%s/" % slug,
                          canonical_path="%s/" % slug))
    for slug, meta in pages_meta["policies"].items():
        body_html = (CONTENT / "pages" / ("policy-%s.html" % slug)).read_text(encoding="utf-8")
        write(ROOT / "policies" / slug / "index.html",
              simple_page(site, slug, meta, body_html, "../../",
                          canonical_path="policies/%s/" % slug))

    write(ROOT / "404.html", not_found_page(site))

    # search index
    idx = [{"slug": e["slug"], "term": e["term"], "acronym": e.get("acronym", ""),
            "synonyms": e.get("synonyms", []), "subjects": e["subjects"],
            "definition": e["plain_definition"], "state": e["editorial_state"]}
           for e in entries]
    write(ROOT / "search-index.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))

    # sitemap and robots
    urls = ["%s/" % base, "%s/dictionary/" % base, "%s/subjects/" % base]
    urls += ["%s/subjects/%s/" % (base, s["slug"]) for s in subjects]
    urls += ["%s/%s/" % (base, slug) for slug in pages_meta["pages"]]
    urls += ["%s/policies/%s/" % (base, slug) for slug in pages_meta["policies"]]
    urls += ["%s/terms/%s/" % (base, e["slug"]) for e in entries
             if e["editorial_state"] in ("published", "draft", "withdrawn")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("  <url><loc>%s</loc><lastmod>%s</lastmod></url>" % (esc(u), BUILD_DATE))
    sm.append("</urlset>")
    write(ROOT / "sitemap.xml", "\n".join(sm) + "\n")
    write(ROOT / "robots.txt",
          "User-agent: *\nAllow: /\nDisallow: /tools/\nDisallow: /content/\nSitemap: %s/sitemap.xml\n" % base)

    print("entries: %d" % len(entries))
    print("subject pages: %d" % len(subjects))
    print("static pages: %d" % (len(pages_meta["pages"]) + len(pages_meta["policies"])))
    print("sitemap urls: %d" % len(urls))


if __name__ == "__main__":
    main()

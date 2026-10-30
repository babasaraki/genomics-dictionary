# Requirements traceability

Source: *The Genomics Dictionary — project concept and website development brief*, version 1,
8 October 2026. This table records what the static GitHub Pages build delivers, what it deliberately
does not, and what needs a server before the first production release.

Status key: **Delivered** — implemented and checked in `docs/ACCEPTANCE-REPORT.md`.
**Partial** — the public behaviour exists, the staff-side behaviour does not.
**Needs server** — cannot exist in a static site; specified here for the implementer.
**Owner decision** — blocked on a decision listed in section 13 of the brief.

## 3 Scope and release priorities

| Brief | Status | Notes |
|---|---|---|
| 3.1 100–150 approved English entries | Delivered | 200 entries, each reviewed and approved by the scientific lead (Dr Umar Ahmad) on 30 October 2026 and published with a recorded reviewer, reviewed revision and next-review date. |
| 3.1 Tested with 1,000 representative records | Partial | Built and searched with 200. The generator and client-side search are linear in entry count; a 1,000-record load test belongs with the production platform. |
| 3.1 Import pilot entries as drafts | Delivered | `tools/import_entries.py` imports CSV/JSON as drafts with a dry run and row-level errors. The 24 pilot entries were not reachable (the prototype is behind a sign-in) and were not imported. |
| 3.2 Eight-subject taxonomy, entries in several subjects | Delivered | `content/subjects.json`; subjects are editable without code changes. |
| 3.2 Empty categories omitted or marked forthcoming | Delivered | Subject index hides zero-count subjects and lists them as forthcoming. |
| 3.3 No peer-review claim unless the process supports it | Delivered | Each entry names the reviewer who approved it and the revision reviewed; the site claims editorial review by a named scientific lead, not external peer review. `validate.py` blocks publication without a reviewer record and blocks a review claim on an unreviewed entry. |

## 4 Website structure and pages

| Brief | Status | Notes |
|---|---|---|
| 4.1 Navigation: Dictionary, Browse subjects, About, Contribute, Donate | Delivered | Plus accessible mobile menu preserving all routes. |
| 4.1 Footer: editorial, privacy, terms and reuse, accessibility, contact, donation information | Delivered | All five policy pages exist. |
| 4.1 Routes `/`, `/dictionary`, `/terms/{slug}`, `/subjects/{slug}`, `/about`, `/contribute`, `/donate`, `/report-error`, `/contact`, `/policies/{slug}` | Delivered | Exactly these paths; each term has its own crawlable URL. |
| 4.1 `/admin` editorial workspace | Needs server | Authenticated workspace with roles; see section 7 below. |
| 4.2 Search above the fold, counts from published records, no unsupported claims | Delivered | Counts computed at build time; no partner logos, user numbers or endorsements anywhere. |
| 4.2 Result cards with term, acronym, definition, subjects, status; 20 per page; filters preserved | Delivered | Pagination of 20 with filter state in the URL. |
| 4.3 Term page order, credits, review date, revision, copy link, print, report error, citation | Delivered | Report-error link carries term, entry id and revision. |
| 4.3 Withdrawn entries stay at their URL; renamed slugs redirect permanently | Delivered | `withdrawn_reason` / `replacement_slug`; `previous_slugs` generates redirect pages. A static host cannot emit a 301 status, so the redirect is a canonical link plus meta refresh — a server or CDN rule should replace it in production. |
| 4.4 Cream background, deep green accents, restrained typography | Delivered | `assets/css/style.css`. Design mockups for sign-off are an implementer deliverable. |

## 5 Content model

| Brief | Status | Notes |
|---|---|---|
| 5.1 Full entry schema with immutable ID separate from slug | Delivered | `GD-####` ids; `entry.schema.json` and `tools/validate.py` enforce the model. |
| 5.1 Version history and restore of a previous revision | Partial | `revision` field plus Git history of `content/terms.json`. A database-backed revision table with one-click restore needs the CMS. |
| 5.2 References stored separately from reviewer approval | Delivered | `references` and `reviewer` are separate fields; the term page states that a source link is not evidence of review. |
| 5.2 Term-specific references preferred over a glossary homepage | Delivered | 304 verified references: 65 journal articles, 228 NHGRI Talking Glossary term pages and 11 resource pages. Verification is logged per reference in `docs/reference-url-check.csv`: the 239 web pages were each requested over HTTP and returned 200, and each of the 65 DOIs was resolved through the Crossref API (status 200, real title and year retrieved). The NHGRI candidate list was harvested from the glossary index and then checked page by page; one harvested URL (Next-Generation-DNA-Sequencing) returned HTTP 503 on repeated requests, so it was removed from the pool and the eight entries citing it were re-pointed at the NHGRI DNA Sequencing page. The validator rejects any reference outside that pool. |
| 5.2 Licence approved by owner before publication | Owner decision | `licence.state` is `not-approved`; the reuse policy says so rather than asserting a licence. |
| 5.3 Scientific language rules | Delivered | Written into the authoring specification and applied across all 200 entries. |
| 5.4 CSV/JSON import with dry run and row-level errors; no silent overwrite | Delivered | `tools/import_entries.py` refuses approved/published records unless explicitly allowed. |
| 5.4 Export entries, categories, references, revision history | Partial | `tools/export_csv.py` exports entries, references and subjects. Contributor records and full revision history come from Git, not a table. |

## 6 Search and discovery

| Brief | Status | Notes |
|---|---|---|
| 6.1 Case-insensitive matching across terms, acronyms, synonyms, definitions | Delivered | |
| 6.1 Punctuation normalisation (whole genome / whole-genome) | Delivered | Checked in D03. |
| 6.1 Ranking: exact term, then acronym/synonym, prefix, broader text | Delivered | Implemented in `assets/js/search.js`. |
| 6.1 Autocomplete up to eight entries, acronym expanded | Delivered | Submitting the query still works if suggestions fail. |
| 6.1 Typo tolerance never silently replaces the query | Delivered | "Did you mean" is shown explicitly on the no-result screen; the query is not rewritten. |
| 6.2 Combined query, subject and letter filters; active filters; one reset | Delivered | |
| 6.2 Numeric/symbol grouping; empty letters disabled | Delivered | 0-9 group appears only when such entries exist. |
| 6.2 State in the URL; Back restores it; count announced accessibly | Delivered | `history.pushState` plus an `aria-live` status region. |
| 6.3 No-result screen offers alternatives and invents no definition | Delivered | |
| 6.4 Reference tests (WGS, VUS, CNV, case, hyphenation, nonsense, intersection, no draft leakage) | Delivered | D03–D05 in the acceptance report. Draft leakage is inverted here: the corpus is entirely draft and labelled as such, and the reviewed-only filter is the control. |

## 7 Editorial workspace

| Brief | Status | Notes |
|---|---|---|
| 7.1 Six roles with server-enforced permissions, including on API endpoints | Needs server | Git review approximates separation of author and reviewer; it is not server-enforced access control. |
| 7.2 Draft → submitted → under review → changes requested → approved → published, withdrawn | Delivered (model) | States exist and are validated; the transitions are performed by editing content, not through a UI. |
| 7.2 Review attaches to the exact revision; material change invalidates approval | Partial | `revision` is recorded; automatic invalidation on edit needs the CMS. |
| 7.2 Publication requires mandatory fields, reviewer approval and next review date | Delivered | `tools/validate.py` refuses to pass a published entry that is missing any of them, and rejects reviewer == contributor. |
| 7.3 Dashboard: assignments, overdue reviews, reported errors, broken relationships, scheduling, notifications | Needs server | Broken-relationship and missing-reference detection already exists in the validator and can be reused. |
| 7.3 Editing homepage text, navigation, policies and donation copy without Git | Needs server | Today these live in `content/`, which requires a commit. |
| 7.4 AI may assist but cannot confer reviewed status or publish | Delivered | Drafting was AI-assisted and is recorded in the `contributor` field of every entry; reviewed status was conferred only by the named human reviewer recorded in `reviewer`, against a specific revision. |

## 8 Donations

| Brief | Status | Notes |
|---|---|---|
| 8.1 Donate in navigation, homepage support section and dedicated page; voluntary wording; no prompts inside definitions | Delivered | No donation prompt appears on any term page. |
| 8.2 One verified hosted provider; website never collects card details | Owner decision | `donation.state` is `not-configured`; no recipient or provider has been approved, and the site says exactly that. |
| 8.3 Donation states (not configured, checkout available, abandoned, pending, confirmed, failed, refunded) | Partial | `not-configured`, `paused` and `checkout-available` are implemented. States that depend on transaction outcomes require the provider integration. |
| 8.4 Webhook-verified ledger, idempotent handling, signature verification | Needs server | Specified in the brief; impossible in a static site. A hosted payment link needs none of it. |
| 8.5 Receipts, donor acknowledgement choices, no unauthorised disclosure | Delivered (policy) | Donation information policy states the position; provider settings implement it. |

## 9–10 Architecture, quality, security, analytics

| Brief | Status | Notes |
|---|---|---|
| 9.1 Structured CMS, editorial workspace, hosted donation service | Needs server | This build is the public half: a structured corpus, a generator and the published site. |
| 9.2 Crawlable primary content; cache invalidation on publication | Delivered | Static HTML is inherently crawlable; publishing regenerates affected pages. |
| 9.3 Staging separate from production, excluded from indexing | Needs server | A second repository or branch deployment plus `robots` exclusion. |
| 9.4 Owner controls domain, hosting, repository, accounts; full source delivered | Delivered | Everything is in this repository; no proprietary components. |
| 10.1 WCAG 2.2 AA target; 360/768/1440 px; 200% zoom; search under one second | Partial | Semantics, keyboard operation, focus, labels and live regions are built in; browser-based verification is outstanding and marked NOT ASSESSED. |
| 10.2 HTTPS, authentication, input validation, rate limits, spam controls | Needs server | GitHub Pages provides HTTPS. There is no authentication surface and no server endpoint to attack; form handling arrives with the form service. |
| 10.2 Forms warn against patient data and collect only what is needed | Delivered | |
| 10.3 Backups, retention, restore demonstration | Partial | Git history is the backup for content; a restore demonstration belongs to the production platform. |
| 10.4 Analytics: visits, term views, unsuccessful searches, outbound donation clicks | Needs server | No analytics are installed; `analytics.provider` is null. The brief's warning that an outbound click is not a confirmed donation is carried into the donation policy. |
| 10.4 Editable titles and descriptions, canonical URLs, sitemap, correct codes, no fabricated structured data | Delivered | Per-page titles and descriptions, canonical links, `sitemap.xml`, `robots.txt` and `DefinedTerm` JSON-LD with no ratings, approvals or endorsements. |

## Outstanding owner decisions (brief section 13)

Legal or institutional owner; final domain; editorial appointments; which entries form the reviewed
launch corpus; donation recipient, provider and currency; reuse licence; privacy and retention
positions once jurisdiction and providers are known; operating budget. Each is represented in the
build by a visible placeholder rather than an invented value.

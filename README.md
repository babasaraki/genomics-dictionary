# The Genomics Dictionary — website

Open-access, searchable dictionary of genomics terminology. Every entry carries a plain-language
definition, a technical explanation, a practical example, a common misunderstanding, related concepts
and references, following the content model in the project development brief (v1, 8 October 2026).

The site is **plain static HTML**. GitHub Pages serves the committed files as they are; the Python
generator runs on your machine, not on GitHub, so the published site can never fail to build.

> **Status: reviewed corpus.** The 200 entries in `content/terms.json` were drafted with AI assistance
> and reviewed and approved by the project's scientific lead, Dr Umar Ahmad, on 30 October 2026. Each
> entry records the reviewer, the revision reviewed, the review date and a next-review date of
> 30 October 2027. Drafting provenance (`contributor`) and review approval (`reviewer`) are separate
> fields, so neither can be mistaken for the other, and `tools/validate.py` refuses to pass a published
> entry that is missing a reviewer, a review date or a next-review date.

## Quick start

```bash
git clone <this repository>
cd genomics-dictionary
python3 tools/validate.py      # checks the corpus against the content model
python3 tools/build.py         # regenerates every HTML page from content/
python3 -m http.server 8000    # preview at http://localhost:8000
```

No third-party Python packages are needed — the standard library is enough.

## Publishing to GitHub Pages

1. Set `base_url` and `repository_url` in `content/site.json` to the real addresses, then re-run
   `python3 tools/build.py` (these values are used for canonical links and the sitemap).
2. Push to `main`.
3. In the repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. The workflow in `.github/workflows/deploy-pages.yml` validates the corpus, confirms that the
   committed HTML matches the content, and deploys. A mismatch fails the build rather than publishing
   stale pages.

For a custom domain, add a `CNAME` file at the repository root containing the bare domain, point a DNS
`CNAME` record at `<user>.github.io`, and update `base_url`.

## Repository layout

```
content/site.json          site title, base URL, donation state, form endpoint, licence state
content/subjects.json      the eight subject areas and their introductions
content/terms.json         the entry corpus — the source of truth
content/references.json    verified reference pool (every URL checked, every DOI resolved)
content/pages/*.html       body copy for About, Contribute, Donate, Contact, policies
tools/build.py             generator: writes index.html, dictionary/, terms/, subjects/, policies/, sitemap
tools/validate.py          content model and publication rules, row-level error report
tools/import_entries.py    CSV/JSON import with dry run; refuses to overwrite reviewed records
tools/export_csv.py        exports entries, references and subjects to exports/*.csv
assets/                    stylesheet, search script, logo
docs/REQUIREMENTS-TRACEABILITY.md   brief section → what is delivered here → what needs a server
```

Everything outside `content/`, `tools/`, `assets/`, `docs/` and `.github/` is generated. The build is
deterministic: page footers and `sitemap.xml` carry the latest date recorded in the corpus, not the
date the generator ran, so rebuilding on another day changes nothing. Do not hand-edit
`index.html`, `terms/`, `subjects/`, `dictionary/`, `policies/`, `search-index.json` or `sitemap.xml`.

## Adding or changing an entry

1. Edit `content/terms.json`. Keep `entry_id` immutable; it is independent of the slug.
2. Required fields: `slug`, `term`, `plain_definition` (40–80 words), `technical_explanation`
   (100–250 words), `practical_example` (40–90 words), `common_misunderstanding` (30–80 words),
   `subjects`, `references` (at least two, each an id present in `content/references.json`),
   `related` (slugs that exist), `editorial_state`, `revision`, `created`, `updated`, `language`.
3. Run `python3 tools/validate.py`, fix anything it reports, then `python3 tools/build.py`.
4. Commit `content/` and the regenerated HTML together.

Renaming a term: change `slug`, add the old value to `previous_slugs`, rebuild. The generator writes a
redirect page at the old address so existing links keep working.

Withdrawing an entry: set `editorial_state` to `withdrawn`, add `withdrawn_reason` and, where relevant,
`replacement_slug`. The entry stays at its URL with an explanation instead of disappearing.

## Editorial review without a CMS

Until the editorial workspace described in section 7 of the brief exists, review runs through Git:

| Brief requirement | How it works here |
|---|---|
| Draft, submitted, under review, changes requested, approved, published, withdrawn | `editorial_state` on each entry |
| Review attaches to a specific revision | `revision` increments on change; approval records the revision reviewed |
| Author cannot approve their own entry | Pull request review by a different person; `validate.py` rejects `reviewer == contributor` |
| Publication needs mandatory fields, reviewer and next review date | `validate.py` refuses to pass a `published` entry missing any of them |
| Public content unchanged while a revision is in draft | Only merged, rebuilt commits reach the site |
| Audit history | Git history of `content/terms.json` |

What Git cannot provide: server-enforced roles, assignment and notification, an editorial dashboard,
scheduled publication, or non-technical editing in a browser. Those need the CMS — see
`docs/REQUIREMENTS-TRACEABILITY.md`.

## Configuration

**Donations.** `content/site.json` → `donation.state` is one of `not-configured` (current), `paused` or
`checkout-available`. Only `checkout-available` shows a payment action, and it requires `recipient`,
`currency` and a `checkout_url` pointing at the approved provider's hosted page. The site never collects
card details and never treats a return from a provider as proof of payment.

**Forms.** `content/site.json` → `form_endpoint`. While it is `null`, the suggestion, correction and
contact forms display that no submission service is connected rather than pretending to store a message.
Set it to a hosted form endpoint to activate them.

**Licence.** `licence.state` is `not-approved`. The reuse policy says so explicitly; set it once the
owner has approved a licence.

## Accessibility and performance

Target WCAG 2.2 AA. Built in: skip link, landmarks, keyboard-operable navigation and filters, visible
focus, labelled fields, live-region result counts, 200% zoom support, and a print stylesheet. The
dictionary page lists every entry as an ordinary link, so content and search-engine visibility do not
depend on JavaScript. Full manual and screen-reader testing is still outstanding and is recorded in the
accessibility policy page when done.

The site ships no fonts, no frameworks and no trackers: a stylesheet, two small scripts and one JSON
search index.

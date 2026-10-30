# Going live on GitHub Pages — step by step

Start to finish: a new repository, a first deploy, and the routine for publishing changes afterwards.
Two routes are given for the Git steps — the command line, or GitHub Desktop if you prefer a window.
Everything else is identical.

Replace `YOUR-USERNAME` with your GitHub account name throughout.

---

## Fast path (one command)

If you would rather not follow the steps by hand: create the empty repository on GitHub first
(step 1 below — name it `genomics-dictionary`, Public, no README, no .gitignore, no licence), then
from inside the unzipped folder run

```bash
./setup-repo.sh YOUR-GITHUB-USERNAME
```

The script writes the correct site address into `content/site.json`, validates the corpus, rebuilds
every page, runs the acceptance checks, then commits and pushes. It refuses to push if validation
fails, and it stops with instructions if Git has no author identity configured. Two browser steps
remain afterwards — switching the Pages source to GitHub Actions, and watching the first run — and
the script prints the exact links for both.

Pass a second argument to use a different repository name, for example
`./setup-repo.sh YOUR-GITHUB-USERNAME YOUR-GITHUB-USERNAME.github.io` for an account-root site.

The sections below are the same sequence done manually, with troubleshooting.

---

## Step 0 — Unpack the site

Download `genomics-dictionary.zip` and unzip it. You get a folder named `genomics-dictionary`
containing `index.html`, `content/`, `tools/`, `assets/`, `docs/` and `.github/`.

Open a terminal in that folder:

```bash
cd path/to/genomics-dictionary
ls        # you should see index.html, content, tools, assets, docs
```

Confirm the hidden files survived unzipping — they matter:

```bash
ls -a | grep -E '^\.(nojekyll|github|gitignore)$'
```

All three must be listed. `.nojekyll` stops GitHub trying to run Jekyll over the site, and
`.github/` holds the deployment workflow. If they are missing, unzip again with a tool that keeps
dotfiles (on macOS, the built-in Archive Utility is fine; some third-party tools strip them).

---

## Step 1 — Create the repository on GitHub

1. Go to <https://github.com/new>.
2. **Repository name**: `genomics-dictionary`.
3. **Description**: *Open-access dictionary of genomics terminology.*
4. **Visibility**: **Public**. (GitHub Pages works on private repositories only on paid plans.)
5. Leave **Add a README**, **Add .gitignore** and **Choose a license** all **unticked** — the folder
   already has its own files, and an auto-created README would collide on the first push.
6. Click **Create repository**.

GitHub now shows an empty repository page with setup instructions. Keep that tab open.

> **Naming note.** `genomics-dictionary` gives you a *project site* at
> `https://YOUR-USERNAME.github.io/genomics-dictionary/`. If you would rather the dictionary sit at the
> root of your account — `https://YOUR-USERNAME.github.io/` — name the repository
> `YOUR-USERNAME.github.io` instead, and use that address as the base URL in step 2. Be aware that a
> user site takes over your whole account address, so do not use it if you already publish something
> else there.

---

## Step 2 — Set the site address, then rebuild

This is the one step that must happen **before** the first push. The base URL is written into every
canonical link, the sitemap and the suggested citation on each entry; if it is wrong, search engines
and citations point at a non-existent address.

Open `content/site.json` and edit the first two values:

```json
"base_url": "https://YOUR-USERNAME.github.io/genomics-dictionary",
"repository_url": "https://github.com/YOUR-USERNAME/genomics-dictionary",
```

No trailing slash on `base_url`. Then regenerate the site and check it:

```bash
python3 tools/validate.py          # expect: checked 200 entries / no problems found
python3 tools/build.py             # expect: entries: 200 ... sitemap urls: 221
python3 tools/acceptance_check.py  # expect: 26 checks, 0 failed
```

Preview locally before anything is public:

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>, search for `WGS`, open an entry, try a subject filter, then stop the
server with `Ctrl+C`.

---

## Step 3 — Put the files under Git and push

### Route A — command line

```bash
git init -b main
git add .
git commit -m "The Genomics Dictionary: initial site with 200 draft entries"
git remote add origin https://github.com/YOUR-USERNAME/genomics-dictionary.git
git push -u origin main
```

If this is the first time Git has run on this machine, set your identity once before committing:

```bash
git config --global user.name "Umar Ahmad"
git config --global user.email "you@example.org"
```

If the push asks for a password, GitHub wants a **personal access token**, not your account password:
<https://github.com/settings/tokens> → *Generate new token (classic)* → tick **repo** → copy the token
and paste it as the password. Easier alternative: install the GitHub CLI (`brew install gh`), run
`gh auth login`, and push again.

### Route B — GitHub Desktop

1. **File → Add Local Repository…**, choose the `genomics-dictionary` folder.
2. When it says the folder is not a Git repository, click **create a repository**, then **Create
   Repository**.
3. Type a summary — *Initial site with 200 draft entries* — and click **Commit to main**.
4. Click **Publish repository**, untick **Keep this code private**, and publish.

---

## Step 4 — Turn on Pages

1. Open `https://github.com/YOUR-USERNAME/genomics-dictionary/settings/pages`.
2. Under **Build and deployment → Source**, change **Deploy from a branch** to **GitHub Actions**.
   The change takes effect immediately; there is no Save button.

GitHub creates a `github-pages` environment that only `main` may deploy to.

---

## Step 5 — Watch the first deployment

1. Open the **Actions** tab.
2. The run named *Deploy to GitHub Pages* appears. It has two jobs: `check` validates the corpus and
   confirms the committed HTML matches `content/`, then `deploy` publishes.
3. Two to three minutes later both show a green tick, and the run summary shows the live address.

Your site is at `https://YOUR-USERNAME.github.io/genomics-dictionary/`.

If `check` fails with *"The generated site differs from the committed files"*, you edited content
without rebuilding. Run `python3 tools/build.py`, commit the result, and push again. The generator is
deterministic — its output depends only on `content/`, never on the day it runs — so a rebuild on
GitHub matches your commit byte for byte as long as you rebuilt after your last content edit.

If the `deploy` job fails — the run reaches "Failed to deploy to github-pages" — the cause is almost
always one of these three, in order of likelihood:

1. **Pages was never enabled**, or its Source is still *Deploy from a branch*. Do step 4. The workflow
   also asks GitHub to enable Pages itself (`configure-pages` with `enablement: true`), which covers
   the case where the setting was never touched.
2. **The repository is private** on a plan without Pages for private repositories. Make it public:
   Settings → General → Danger Zone → Change visibility.
3. **Actions lacks write permission.** Settings → Actions → General → Workflow permissions →
   *Read and write permissions*.

Re-run from the Actions tab after any of these.

---

## Step 6 — Check the live site

Open the published address and confirm:

- the homepage loads with the search box and the eight subject cards;
- searching `VUS` returns *Variant of uncertain significance* first;
- an entry page opens at its own URL, and reloading that URL works;
- `https://YOUR-USERNAME.github.io/genomics-dictionary/sitemap.xml` lists 221 URLs;
- a deliberately wrong address shows the project's own "Page not found" page;
- the draft banner appears on every page.

Then submit the sitemap to Google Search Console (optional, and only once you are content for the
site to be indexed — remember the whole corpus is still unreviewed).

---

## Step 7 — Publishing changes from now on

```bash
# 1. edit content/terms.json, or a page in content/pages/
python3 tools/validate.py     # must pass before you continue
python3 tools/build.py        # regenerates the affected HTML
git add .
git commit -m "Revise the reference genome entry after review"
git push
```

The workflow redeploys automatically. Never hand-edit the generated files (`index.html`, `terms/`,
`subjects/`, `dictionary/`, `policies/`, `sitemap.xml`, `search-index.json`) — the next build
overwrites them, and the drift check will fail the deployment.

**Reviewing before publishing.** Work on a branch, open a pull request, and have the scientific
reviewer approve it. Nothing reaches the live site until the pull request is merged into `main`:

```bash
git checkout -b review/reference-genome
# ... edit, validate, build, commit ...
git push -u origin review/reference-genome
```

---

## Optional — a custom domain

1. Buy the domain, then at your DNS provider add a `CNAME` record pointing
   `www.yourdomain.org` at `YOUR-USERNAME.github.io`. For a bare domain
   (`yourdomain.org`) add four `A` records instead, pointing at `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153` and `185.199.111.153`.
2. In **Settings → Pages → Custom domain**, enter the domain and save. GitHub commits a `CNAME`
   file to the repository.
3. Tick **Enforce HTTPS** once the certificate has been issued (this can take up to an hour).
4. Update `base_url` in `content/site.json` to the new address, then rebuild, commit and push so
   canonical links and citations follow the domain.

---

## Before you tell anyone the address

The 200 entries carry a recorded review by the project's scientific lead. Section 3.3 of the project
brief is satisfied — the site claims editorial review by a named reviewer, not external peer review —
but a few things are still placeholders. Before a public launch:

- consider adding subject reviewers for the areas outside the lead's closest expertise, so that each
  subject carries a second recorded opinion;
- fill in the owner, editorial team and contact placeholders on the About and policy pages;
- decide the reuse licence and set `licence.state`;
- connect a form service (`form_endpoint`) so suggestions and error reports actually arrive;
- leave `donation.state` as `not-configured` until a recipient and provider are approved.

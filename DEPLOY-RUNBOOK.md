# Ivory Road Site: Deployment Runbook

Status as of 2026-09-06. The site is built and pushed. What remains is
connecting Cloudflare and cutting over DNS.

## The architecture, in one paragraph

The site is a dependency-free Python generator. `build.py` reads page fragments
and article files and writes a complete static site to `dist/`. The source lives
in GitHub at `sfuller211/ivoryroad-site`. Cloudflare Pages watches that repo,
runs `python3 build.py` itself, and serves the result. Payhip handles digital
checkout. Amazon handles print. Nothing is uploaded by hand.

## Done

- Site built: 32 pages, 17 live articles, 21 MB output
- 21 redirects from the old Shopify URLs
- Structured data, sitemap, robots.txt, RSS feed
- Metadata on every page
- Repo pushed to GitHub, 132 files, branch `main`
- Verified: a fresh clone builds correctly with no local files

Auth to GitHub is an SSH deploy key with write access, scoped to that one repo.
The key pair is in `Desktop\Ivory Road Cowork\_keys\` with revoke instructions.
No password or token was ever shared.

## Before connecting Cloudflare

**Resolve the duplicate article.** `when-teen-son-feels-alone` is scheduled for
2026-09-07 and is a near-duplicate of the already-live
`when-teen-son-feels-alone-what-parents-miss`. Publishing is date-driven, so the
first Cloudflare build will publish it automatically. Retitle it, merge the two,
or set its status to `draft` in `_export/articles-meta.tsv`.

**Decide repo visibility.** Recommendation is private. Nothing sensitive is in
the repo, but three scheduled articles and four unpublished drafts are currently
readable by anyone. Cloudflare Pages, GitHub Actions, and the deploy key all
work fine on a private free-tier repo.

## Steps, in order

Nothing live is touched until step 4.

**1. Connect Cloudflare Pages**

Workers & Pages > Create > Pages > Connect to Git > `ivoryroad-site`

| Setting | Value |
|---|---|
| Framework preset | None |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Root directory | blank |

Cloudflare's build image ships Python 3.13. `build.py` uses only the standard
library, so there is nothing to install.

**2. Wire the Monday trigger**

Cloudflare > the project > Settings > Builds & deployments > Deploy hooks >
Add deploy hook, branch `main`. Copy the URL.

GitHub > repo > Settings > Secrets and variables > Actions > New repository
secret, named exactly `CF_DEPLOY_HOOK`. Paste.

This is what makes scheduled articles publish themselves. Until it exists the
weekly workflow fails with a clear message and deploys nothing.

**3. Review the `.pages.dev` preview**

Cloudflare gives a free preview URL. Check the pages, the article index, the
redirects, and the Payhip links before touching DNS.

**4. Point the domain**

ivoryroad.shop is registered at Squarespace Domains, not Shopify. Point it at
Cloudflare and confirm HTTPS goes green.

**5. Repoint the domain forwards**

blueprintbooks.net currently forwards to `/collections/books`, which stops
existing. Send it to `/pages/real-talk`. rubydoodle.net goes to
`/pages/ruby-doodle`.

**6. Only then cancel Shopify**

Two things to fix on Shopify first, since they only matter while it is up:
Enchanted Realms `custom.amazon_link` should be
`https://www.amazon.com/dp/B0CP2V93L2`, and its title should say "A Coloring
Odyssey" not "A Coloring Journey".

## After it is live

Publishing an article is: add the body, the image, and one row to
`_export/articles-meta.tsv` with status `scheduled` and a future Monday. It
publishes itself. See "Weekly Blog Workflow" for the detail.

Any push to `main` deploys within a couple of minutes.

## If something breaks

- Build fails on Cloudflare: the build log names the file. `python3 build.py`
  locally reproduces it exactly.
- Monday post did not appear: check the Actions tab. A red run usually means
  `CF_DEPLOY_HOOK` is missing or was regenerated on the Cloudflare side.
- Need to publish immediately: GitHub > Actions > Weekly publish > Run workflow.
- Revoke Claude's push access: GitHub > repo > Settings > Deploy keys > delete.
  The `_keys` folder can then be deleted too.

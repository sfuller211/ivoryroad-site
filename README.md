# ivoryroad-site

The Ivory Road website. Plain Python, no dependencies, no build tooling.

## What is here

| Path | What it is |
|---|---|
| `build.py` | The whole generator. Python 3 standard library only. |
| `content/pages/` | Page bodies as HTML fragments. |
| `static/css/` | Site stylesheet. |
| `_export/articles-meta.tsv` | One row per blog article. |
| `_export/bodies/` | Article bodies as HTML. |
| `_export/images/` | Every image on the site. |
| `_export/qr/` | Print-ready review QR codes. Not published to the site. |
| `dist/` | Generated output. Not committed. |

## Build

```
python3 build.py
```

Writes `dist/`, ready to serve as-is.

## Cloudflare Pages settings

| Setting | Value |
|---|---|
| Framework preset | None |
| Build command | `python3 build.py` |
| Build output directory | `dist` |
| Root directory | (leave blank) |

Cloudflare's build image ships Python 3.13. `build.py` uses only the standard
library, so there is nothing to install.

## Publishing an article

See `WEEKLY-BLOG.md`. Short version: add the body, the image, and one row to
`_export/articles-meta.tsv` with status `scheduled` and a future Monday. It
publishes itself on the first build after that date.

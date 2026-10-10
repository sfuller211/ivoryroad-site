# Weekly blog workflow

One article goes out every Monday. Here is the whole system.

## What the builder does for you

`build.py` reads three things and generates everything else:

| You provide | Where it goes |
|---|---|
| The article body as HTML | `_export/bodies/<handle>.html` |
| The hero image | `_export/images/<handle>.jpg` |
| One row of metadata | `_export/articles-meta.tsv` |

From that it generates the article page, the entry on the articles index, the
topic chip and search text, the RSS feed, the sitemap entry, the meta title and
description, and the Article structured data. You never edit those by hand.

## The metadata row

Nine tab-separated columns:

```
handle  published  status  image_url  alt  title  topic  seo_title  meta_description
```

- **handle** is the URL slug and must match the body filename and the image filename
- **published** is `YYYY-MM-DD`
- **status** is `live`, `scheduled`, or `draft`
- **image_url** is only kept for reference; the build uses the local image
- **seo_title** is the page `<title>` that shows in search results. Keep it to 60 characters or fewer, lead with the phrase a parent would type, no brand suffix. The article H1 stays as **title**.
- **meta_description** is the search snippet. 155 characters or fewer. Say what the post is about and who it helps. Do not paste the opening lines of the post. If either column is blank the build falls back to the old behavior (title plus " | Ivory Road", description from the first paragraph).
- **topic** must be one of: Identity, Emotions, Confidence, Faith, Relationships,
  Connection, Behind the Series

## Scheduling

Set **status** to `scheduled` and give it a future Monday. The article stays
invisible until that date arrives, then publishes itself on the next build.
No code change, no flag to flip.

- `live` publishes always
- `scheduled` publishes once its date arrives
- `draft` never publishes, whatever the date

Every build prints what is still queued:

```
Built 32 pages (17 live articles)
  queued for 2026-09-07: when-teen-son-feels-alone
  queued for 2026-09-14: stay-connected-teen-son-goes-quiet
  queued for 2026-09-21: small-signs-teen-son-opening-up
```

## The recommended rhythm

Write in batches, publish weekly.

**Once a month or once a quarter:** write four to twelve articles, drop in the
bodies and images, add the rows as `scheduled` with consecutive Mondays.

**Every Monday:** run `python3 build.py`, then redeploy. Nothing else. The
article that came due publishes itself.

Batching is what makes this sustainable. The weekly step is two minutes.

## Deploying

You do not deploy. Cloudflare does.

The repo is connected to Cloudflare Pages. Cloudflare runs `python3 build.py`
itself and publishes the result. Two things make it rebuild:

1. **You push to GitHub.** Any change goes live in a couple of minutes.
2. **The Monday workflow fires.** `.github/workflows/weekly-publish.yml` pings
   a Cloudflare deploy hook at 12:00 UTC every Monday. That is what makes a
   scheduled article publish itself on the right day with nobody touching
   anything. Your computer does not need to be on.

You can also publish on demand: GitHub, Actions tab, "Weekly publish",
Run workflow.

So the real weekly rhythm is: nothing. You write in batches, queue the dates,
and Monday takes care of itself.

## Notes

- Article titles must be unique. Duplicates make two pages compete in search.
- The hero image should be 1200x675. The builder writes width and height into
  the tag so the page does not jump while loading.
- Adding a topic that is not in the list above means it will not get a filter
  chip. Add it to `TOPIC_ORDER` in build.py first.

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

Seven tab-separated columns:

```
handle  published  status  image_url  alt  title  topic
```

- **handle** is the URL slug and must match the body filename and the image filename
- **published** is `YYYY-MM-DD`
- **status** is `live`, `scheduled`, or `draft`
- **image_url** is only kept for reference; the build uses the local image
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

The site is static, so it cannot publish itself on a schedule. Something has to
push the new `dist/` folder up. Whichever method you use, the Monday step is
build, then deploy.

## Notes

- Article titles must be unique. Duplicates make two pages compete in search.
- The hero image should be 1200x675. The builder writes width and height into
  the tag so the page does not jump while loading.
- Adding a topic that is not in the list above means it will not get a filter
  chip. Add it to `TOPIC_ORDER` in build.py first.

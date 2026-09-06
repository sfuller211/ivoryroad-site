#!/usr/bin/env python3
"""
Ivory Road static site builder.

No dependencies. Python 3 only. Run:  python3 build.py
Output goes to dist/ and is ready to upload to Cloudflare Pages as-is.

URL paths deliberately mirror the old Shopify site so the move reads to Google
as a hosting change rather than a site move:
    /blogs/real-talk-articles/<slug>/
    /pages/<handle>/
"""
import csv, html, json, os, re, shutil, struct, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
EXPORT = ROOT / "_export"
CONTENT = ROOT / "content" / "pages"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

SITE = "https://ivoryroad.shop"
BLOG = "/blogs/real-talk-articles"

# ---------------------------------------------------------------- pages
# (output path, fragment file, <title>, meta description)
PAGES = [
    ("",                      "home.html",           "Ivory Road | Faith-Based Books for Teen Boys & Coloring Books",
     "Faith-based resources for teen boys and their families, and creative coloring books for all ages."),
    ("pages/real-talk",       "real-talk.html",      "Real Talk | Faith-Based Books for Teen Boys | Ivory Road",
     "A faith-based series for teen guys on identity, emotions, confidence, relationships, and real-life faith."),
    ("pages/for-parents",     "for-parents.html",    "For Parents | Real Talk | Ivory Road",
     "Teen boys are hard to read. Real Talk gives you a way back in, and gives him something to work through on his own."),
    ("pages/for-teen-guys",   "for-teen-guys.html",  "For Teen Guys | Real Talk | Ivory Road",
     "Not a textbook. Not a lecture. More like a conversation about the stuff that is hard to say out loud."),
    ("pages/for-leaders",     "for-leaders.html",    "For Youth Leaders | Real Talk Small Group Curriculum | Ivory Road",
     "Twelve session outlines, discussion questions, and facilitator notes for leading teen guys through Real Talk."),
    ("pages/ruby-doodle",     "ruby-doodle.html",    "Ruby Doodle Coloring Books | Ivory Road",
     "Coloring books for people who like to slow down, stay creative, and enjoy a few peaceful minutes."),
    ("pages/free-guides",     "free-guides.html",    "Free Downloads | Ivory Road",
     "Free resources for parents of teen boys and for teen guys themselves. No purchase needed."),
    ("pages/hearts-and-home", "hearts-and-home.html","Real Talk Hearts & Home | Free Guide for Parents | Ivory Road",
     "A free, practical guide to help you connect with your son in real, everyday moments."),
    ("pages/real-talk-tools", "real-talk-tools.html","Real Talk Tools | Free Guide for Teen Guys | Ivory Road",
     "A free set of reflection prompts and tools for teen guys figuring things out."),
    ("pages/about-us",        "about-us.html",       "About Ivory Road",
     "We started Ivory Road because we love working together and we love encouraging others."),
    ("pages/contact",         "contact.html",        "Contact | Ivory Road", "Get in touch with Ivory Road."),
    ("pages/privacy-policy",  "privacy.html",        "Privacy Policy | Ivory Road", "How Ivory Road handles your information."),
    ("pages/real-talk-review", "real-talk-review.html", "Leave a Review | Real Talk | Ivory Road",
     "Leave an honest Amazon review for the Real Talk book you read. Takes about two minutes."),
    ("pages/ruby-doodle-review", "ruby-doodle-review.html", "Leave a Review | Ruby Doodle | Ivory Road",
     "Leave an honest Amazon review for the Ruby Doodle coloring book you colored."),
]

NAV = [
    ("Real Talk",  "/pages/real-talk"),
    ("Ruby Doodle","/pages/ruby-doodle"),
    ("Articles",   BLOG + "/"),
    ("Free Downloads","/pages/free-guides"),
    ("About",      "/pages/about-us"),
]

# Topic assigned to each article, used for the filter on the Articles page.
ARTICLE_TOPICS = {
    "why-we-created-real-talk":                    "Behind the Series",
    "real-talk-for-teen-girls-is-coming":           "Behind the Series",
    "hidden-signs-teen-boy-insecurity":             "Confidence",
    "teen-boy-courage-what-fear-looks-like":        "Confidence",
    "teen-son-feels-different-uniqueness":          "Identity",
    "why-teen-boys-wear-masks":                     "Identity",
    "what-makes-a-man-what-teen-son-believes":      "Identity",
    "what-god-thinks-about-teen-boys":              "Faith",
    "everyday-faith-teen-boys-what-parents-can-do": "Faith",
    "teen-boys-prayer-why-they-go-silent":          "Faith",
    "teen-son-anger-emotional-signals":             "Emotions",
    "teen-son-replaying-mistakes-shame":            "Emotions",
    "teen-boy-failure-what-hes-carrying":           "Emotions",
    "why-teen-boys-blow-up-over-small-things":      "Emotions",
    "what-to-do-after-teen-son-blowup":             "Emotions",
    "teen-boy-conflict-whats-really-happening":     "Relationships",
    "when-teen-son-feels-alone-what-parents-miss":  "Connection",
    "when-teen-son-feels-alone":                    "Connection",
    "stay-connected-teen-son-goes-quiet":           "Connection",
    "small-signs-teen-son-opening-up":              "Connection",
}
TOPIC_ORDER = ["Identity", "Emotions", "Confidence", "Faith", "Relationships",
               "Connection", "Behind the Series"]

# Secondary navigation shown on every Real Talk page, mirroring the live site.
SUBNAV = [
    ("Real Talk",     "/pages/real-talk"),
    ("For Parents",   "/pages/for-parents"),
    ("For Teen Guys", "/pages/for-teen-guys"),
    ("For Leaders",   "/pages/for-leaders"),
    ("Free Downloads","/pages/free-guides"),
    ("Articles",      BLOG + "/"),
]

# ---------------------------------------------------------------- structured data
ORG = {
    "@type": "Organization",
    "@id": SITE + "#organization",
    "name": "Ivory Road",
    "url": SITE + "/",
    "email": "hello@ivoryroad.shop",
    "logo": {"@type": "ImageObject", "url": SITE + "/static/images/ivory-road-logo.png"},
    "sameAs": [
        "https://www.instagram.com/ivoryroadshop",
        "https://www.facebook.com/ivoryroadshop",
        "https://www.pinterest.com/ivoryroadshop/",
        "https://www.tiktok.com/@ivoryroadshop",
        "https://www.youtube.com/@ivoryroadshop",
    ],
}

AUTHOR = {"@type": "Person", "name": "Dr. Scott Fuller",
          "@id": SITE + "#dr-scott-fuller", "jobTitle": "Author"}

# Real books, so Book schema is accurate. No price or availability: nothing is sold on
# this site, and a stale price is worse than no price.
REAL_TALK_BOOKS = [
    ("Real Talk: Becoming Who God Made You to Be", "1970494050",
     "A Christian guide for teen boys on confidence, identity, and faith."),
    ("Real Talk Workbook", "1970494077",
     "The companion workbook, following the student book chapter by chapter."),
    ("Real Talk Parent Guide", "1970494085",
     "A practical guide for parents of teenage boys."),
    ("Real Talk Small Group Leader Guide", "1970494093",
     "A twelve session discipleship guide for youth leaders."),
]

def books_schema():
    items = []
    for i, (name, isbn, desc) in enumerate(REAL_TALK_BOOKS, 1):
        items.append({
            "@type": "ListItem", "position": i,
            "item": {"@type": "Book", "name": name, "isbn": isbn,
                     "description": desc, "author": AUTHOR,
                     "inLanguage": "en", "bookFormat": "https://schema.org/Paperback",
                     "publisher": {"@type": "Organization", "name": "Ivory Road Resources"},
                     "url": "https://www.amazon.com/dp/" + isbn},
        })
    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": "The Real Talk Series", "itemListElement": items}

def home_schema():
    return {"@context": "https://schema.org", "@graph": [
        ORG,
        {"@type": "WebSite", "@id": SITE + "#website", "url": SITE + "/",
         "name": "Ivory Road", "publisher": {"@id": SITE + "#organization"},
         "inLanguage": "en"},
    ]}

def article_schema(a, url, desc):
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "Article",
         "headline": a["title"][:110],
         "description": desc,
         "image": SITE + a["img"],
         "datePublished": a["published"],
         "dateModified": a["published"],
         "author": AUTHOR,
         "publisher": {"@id": SITE + "#organization"},
         "mainEntityOfPage": {"@type": "WebPage", "@id": SITE + url},
         "isPartOf": {"@type": "Blog", "@id": SITE + BLOG + "/",
                      "name": "Real Talk Articles"},
         "inLanguage": "en"},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Real Talk Articles",
             "item": SITE + BLOG + "/"},
            {"@type": "ListItem", "position": 3, "name": a["title"]},
        ]},
    ]}

def jsonld(obj):
    if not obj:
        return ""
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    txt = txt.replace("</", "<\\/")   # never let a closing tag escape the script block
    return '<script type="application/ld+json">' + txt + '</script>\n'

# ---------------------------------------------------------------- image dimensions
_DIMS = {}

def image_size(path):
    """Intrinsic width and height, PNG and JPEG, no third-party libraries."""
    if path in _DIMS:
        return _DIMS[path]
    size = None
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                size = struct.unpack(">II", head[16:24])
            elif head[:2] == b"\xff\xd8":
                fh.seek(2)
                while True:
                    b = fh.read(1)
                    while b and b != b"\xff":
                        b = fh.read(1)
                    marker = fh.read(1)
                    while marker == b"\xff":
                        marker = fh.read(1)
                    if not marker:
                        break
                    if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6,
                                     0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        fh.read(3)
                        h, w = struct.unpack(">HH", fh.read(4))
                        size = (w, h)
                        break
                    seg = struct.unpack(">H", fh.read(2))[0]
                    fh.seek(seg - 2, 1)
    except Exception:
        size = None
    _DIMS[path] = size
    return size

def fix_images(page_html):
    """Add width, height, loading and decoding to any img that is missing them."""
    counter = {"n": 0}

    def repl(m):
        tag = m.group(0)
        counter["n"] += 1
        src = re.search(r'src="([^"]+)"', tag)
        if src and "width=" not in tag and src.group(1).startswith("/static/images/"):
            f = DIST / src.group(1).lstrip("/")
            dims = image_size(f)
            if dims:
                tag = tag[:-1].rstrip() + ' width="{}" height="{}">'.format(*dims)
        if "loading=" not in tag:
            # the logo and the first content image are above the fold; never lazy those
            mode = "eager" if counter["n"] <= 2 else "lazy"
            tag = tag[:-1].rstrip() + ' loading="{}">'.format(mode)
        if "decoding=" not in tag:
            tag = tag[:-1].rstrip() + ' decoding="async">'
        return tag

    return re.sub(r"<img\b[^>]*>", repl, page_html)

# Pages that carry the Real Talk secondary nav.
SUBNAV_PAGES = {
    "pages/real-talk", "pages/for-parents", "pages/for-teen-guys",
    "pages/for-leaders", "pages/free-guides", "pages/hearts-and-home",
    "pages/real-talk-tools",
}

FOOTER = [
    ("Real Talk", [("Real Talk Series","/pages/real-talk"),("For Parents","/pages/for-parents"),
                   ("For Teen Guys","/pages/for-teen-guys"),("For Leaders","/pages/for-leaders"),
                   ("Free Downloads","/pages/free-guides")],
     [("Instagram","https://www.instagram.com/realtalkbookseries/"),
      ("Facebook","https://www.facebook.com/realtalkbookseries"),
      ("TikTok","https://www.tiktok.com/@realtalkbookseries")]),
    ("Ruby Doodle", [("Browse the Collection","https://payhip.com/IvoryRoadDigitalShop"),
                     ("Free Coloring Pages","https://payhip.com/b/EzoB7")], []),
    ("Ivory Road", [("About Us","/pages/about-us"),("Articles",BLOG + "/"),
                    ("Contact","/pages/contact"),("Privacy Policy","/pages/privacy-policy")],
     [("Instagram","https://www.instagram.com/ivoryroadshop"),
      ("Facebook","https://www.facebook.com/ivoryroadshop"),
      ("Pinterest","https://www.pinterest.com/ivoryroadshop/"),
      ("TikTok","https://www.tiktok.com/@ivoryroadshop"),
      ("YouTube","https://www.youtube.com/@ivoryroadshop")]),
]

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
{ogimage}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/static/images/ivory-road-logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/css/site.css">
<link rel="alternate" type="application/rss+xml" title="Real Talk Articles" href="/blogs/real-talk-articles/feed.xml">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{header}
<main id="main">
{body}
</main>
{footer}
</body>
</html>
"""

def header_html():
    links = "".join(
        '<a href="{}">{}</a>'.format(u, html.escape(t)) for t, u in NAV
    )
    return ('<div class="announce">Get both free Real Talk guides for parents &amp; teen guys. '
            '<a href="/pages/free-guides">Download now</a></div>'
            '<header class="site-header"><div class="wrap">'
            '<a class="logo" href="/"><img src="/static/images/ivory-road-logo.png" '
            'alt="Ivory Road" width="150" height="58"></a>'
            '<nav class="nav" aria-label="Primary">{}</nav>'
            '</div></header>').format(links)

def footer_html():
    cols = []
    for name, links, socials in FOOTER:
        li = "".join('<li><a href="{}">{}</a></li>'.format(u, html.escape(t)) for t, u in links)
        soc = ""
        if socials:
            soc = '<div class="social">' + " ".join(
                '<a href="{}" rel="noopener">{}</a>'.format(u, html.escape(t)) for t, u in socials
            ) + "</div>"
        cols.append('<div><h4>{}</h4><ul>{}</ul>{}</div>'.format(html.escape(name), li, soc))
    return ('<footer class="site-footer"><div class="wrap">'
            '<div class="foot-cols">{}</div>'
            '<div class="foot-base"><span>We create things that matter.</span>'
            '<span>&copy; {} Ivory Road LLC. All rights reserved.</span></div>'
            '</div></footer>').format("".join(cols), datetime.now().year)

def subnav_html(current=""):
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(
            u, ' aria-current="page"' if u.rstrip("/") == ("/" + current).rstrip("/") else "",
            html.escape(t))
        for t, u in SUBNAV
    )
    return ('<nav class="subnav" aria-label="Real Talk"><div class="wrap">{}</div></nav>'
            ).format(links)

def render(body, title, desc, canonical, ogtype="website", ogimage=None, subnav=None, published=None, schema=None):
    og = ''
    if ogimage:
        og = '<meta property="og:image" content="{}{}">\n'.format(SITE, ogimage)
    if published:
        og += ('<meta property="article:published_time" content="{}">\n'
               '<meta property="article:author" content="Dr. Scott Fuller">\n'
               '<meta name="author" content="Dr. Scott Fuller">\n').format(published)
    og += jsonld(schema)
    head = header_html()
    if subnav is not None:
        head += subnav_html(subnav)
    page = SHELL.format(title=html.escape(title), desc=html.escape(desc),
                        canonical=canonical, ogtype=ogtype, ogimage=og,
                        header=head, footer=footer_html(), body=body)
    return fix_images(page)

def write(path_parts, content):
    out = DIST.joinpath(*[p for p in path_parts if p]) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out

# ---------------------------------------------------------------- articles
MONTHS = ["January","February","March","April","May","June","July",
          "August","September","October","November","December"]

def pretty_date(iso):
    y, m, d = iso.split("-")
    return "{} {}, {}".format(MONTHS[int(m) - 1], int(d), y)

def load_articles():
    """Read articles-meta.tsv.

    status column: "live", "scheduled", or "draft".
      live       -> always published
      scheduled  -> published automatically once its published date has arrived
      draft      -> never published, whatever the date
    topic column is optional; falls back to ARTICLE_TOPICS then "Real Talk".
    """
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    with open(EXPORT / "articles-meta.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            body_file = EXPORT / "bodies" / (r["handle"] + ".html")
            if not body_file.exists():
                print("  !! missing body:", r["handle"]); continue
            raw = body_file.read_text(encoding="utf-8")
            raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S).strip()
            ext = os.path.splitext(r["image_url"].split("?")[0])[1] or ".jpg"
            r["body"] = raw
            r["img"] = "/static/images/{}{}".format(r["handle"], ext)
            r["topic"] = ((r.get("topic") or "").strip()
                          or ARTICLE_TOPICS.get(r["handle"], "Real Talk"))
            if r["status"] == "scheduled" and r["published"] <= today:
                r["status"] = "live"
            rows.append(r)
    rows.sort(key=lambda x: x["published"], reverse=True)
    return rows

def build_articles(arts):
    live = [a for a in arts if a["status"] == "live"]
    for a in arts:
        if a["status"] != "live":
            continue          # scheduled posts stay unpublished until their date
        url = "{}/{}/".format(BLOG, a["handle"])
        body = """
<article class="section">
  <div class="article">
    <p class="breadcrumb"><a href="{blog}/">Real Talk Articles</a></p>
    <h1>{title}</h1>
    <p class="article__meta">{date} &middot; Dr. Scott Fuller</p>
  </div>
  <figure class="article__hero article"><img src="{img}" alt="{alt}" width="1200" height="675" loading="eager"></figure>
  <div class="article article__body">
{content}
  </div>
</article>
<section class="section s-sage section--edge">
  <div class="narrow center">
    <p class="eyebrow">Real Talk</p>
    <h2>Written for the teen boy who has more going on inside than he is letting on.</h2>
    <p>Four resources: a student book, a workbook, a parent guide, and a leader guide.</p>
    <div class="btns" style="justify-content:center">
      <a class="btn" href="/pages/real-talk">Explore the Series</a>
      <a class="btn btn--ghost" href="/pages/free-guides">Get a Free Guide</a>
    </div>
  </div>
</section>
""".format(blog=BLOG, title=html.escape(a["title"]), date=pretty_date(a["published"]),
           img=a["img"], alt=html.escape(a["alt"]), content=a["body"])
        desc = summarize(a["body"])
        write([BLOG.strip("/"), a["handle"]],
              render(body, a["title"] + " | Ivory Road", desc,
                     SITE + url, ogtype="article", ogimage=a["img"],
                     subnav=BLOG.strip("/"), published=a["published"],
                     schema=article_schema(a, url, desc)))
    return live

def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()

def summarize(body, limit=155):
    """Meta description from the article's opening prose, not the title."""
    for para in re.findall(r"<p[^>]*>(.*?)</p>", body, flags=re.S):
        text = strip_tags(para)
        if len(text) < 40 or text.startswith(("This post was written", "Photo")):
            continue
        if len(text) <= limit:
            return text
        cut = text[:limit]
        stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        if stop > 60:
            return cut[:stop + 1]
        return cut[:cut.rfind(" ")].rstrip(",;:") + "..."
    return strip_tags(body)[:limit]

def build_journal_index(live):
    cards = "".join("""
<a class="post-card" href="{blog}/{h}/" data-topic="{topic}" data-text="{search}">
  <img src="{img}" alt="{alt}" width="800" height="450" loading="lazy">
  <h3>{title}</h3>
  <p class="post-meta"><time datetime="{iso}">{date}</time> <span class="post-topic">{topic}</span></p>
</a>""".format(blog=BLOG, h=a["handle"], img=a["img"], alt=html.escape(a["alt"]),
               iso=a["published"], date=pretty_date(a["published"]),
               topic=html.escape(a["topic"]),
               search=html.escape((a["title"] + " " + a["topic"]).lower()),
               title=html.escape(a["title"])) for a in live)

    used = [t for t in TOPIC_ORDER
            if any(a["topic"] == t for a in live)]
    chips = '<button type="button" data-filter="all" aria-pressed="true">All</button>'
    chips += "".join('<button type="button" data-filter="{0}" aria-pressed="false">{0}</button>'.format(
        html.escape(t)) for t in used)

    body = """
<section class="section section--hero-tight">
  <div class="intro">
    <p class="eyebrow eyebrow--lg">Real Talk Articles</p>
    <h1>Honest writing for parents of teen boys.</h1>
    <p class="lede">Short, practical pieces on what teen guys are carrying, what it looks like from the outside, and how to stay close while they figure it out.</p>
    <div class="topics">{chips}</div>
    <label class="skip" for="article-search">Search articles</label>
    <input id="article-search" class="topic-search" type="search" placeholder="Search articles" autocomplete="off">
  </div>
</section>
<section class="section--tight section--pull">
  <div class="wrap">
    <div class="posts" id="post-grid">{cards}</div>
    <p class="posts-empty" id="posts-empty" hidden>Nothing matches that yet. Try another topic or a different word.</p>
  </div>
</section>

<script>
(function(){{
  var grid = document.getElementById('post-grid');
  if(!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('.post-card'));
  var chips = [].slice.call(document.querySelectorAll('.topics button'));
  var box = document.getElementById('article-search');
  var empty = document.getElementById('posts-empty');
  var topic = 'all';

  function apply(){{
    var q = (box.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){{
      var okTopic = topic === 'all' || c.dataset.topic === topic;
      var okText = !q || c.dataset.text.indexOf(q) > -1;
      var show = okTopic && okText;
      c.hidden = !show;
      if(show) shown++;
    }});
    empty.hidden = shown > 0;
  }}

  chips.forEach(function(b){{
    b.addEventListener('click', function(){{
      topic = b.dataset.filter;
      chips.forEach(function(x){{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
      apply();
    }});
  }});
  box.addEventListener('input', apply);
  apply();
}})();
</script>
""".format(cards=cards, chips=chips)
    write([BLOG.strip("/")], render(body, "Real Talk Articles | Ivory Road",
          "Honest writing for parents of teen boys. Identity, emotions, and real-life faith.",
          SITE + BLOG + "/", subnav=BLOG.strip("/")))

def build_feed(live):
    items = []
    for a in live[:30]:
        url = "{}{}/{}/".format(SITE, BLOG, a["handle"])
        items.append("""  <item>
    <title>{t}</title>
    <link>{u}</link>
    <guid isPermaLink="true">{u}</guid>
    <pubDate>{d}</pubDate>
    <description>{t}</description>
  </item>""".format(t=html.escape(a["title"]), u=url,
                    d=datetime.strptime(a["published"], "%Y-%m-%d").strftime("%a, %d %b %Y 14:00:00 +0000")))
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Real Talk Articles</title>
  <link>{site}{blog}/</link>
  <description>Honest writing for parents of teen boys.</description>
  <language>en-us</language>
{items}
</channel></rss>
""".format(site=SITE, blog=BLOG, items="\n".join(items))
    p = DIST / BLOG.strip("/") / "feed.xml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(feed, encoding="utf-8")

def build_sitemap(urls):
    body = "".join("  <url><loc>{}{}</loc></url>\n".format(SITE, u) for u in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n",
        encoding="utf-8")
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n".format(SITE), encoding="utf-8")

# ---------------------------------------------------------------- main
def main():
    # Rebuild in place. Files are overwritten, not deleted first, because some
    # synced/managed folders disallow unlink. If you rename or remove a page,
    # delete dist/ by hand once and rebuild.
    try:
        if DIST.exists():
            shutil.rmtree(DIST)
    except (PermissionError, OSError):
        print("  note: could not clear dist/, overwriting in place")
    DIST.mkdir(parents=True, exist_ok=True)

    # static assets
    shutil.copytree(STATIC, DIST / "static", dirs_exist_ok=True)
    imgs = DIST / "static" / "images"
    imgs.mkdir(parents=True, exist_ok=True)
    for f in (EXPORT / "images").iterdir():
        if f.is_file():
            shutil.copy2(f, imgs / f.name)

    urls = []

    # static pages
    for path, frag, title, desc in PAGES:
        src = CONTENT / frag
        if not src.exists():
            print("  !! missing fragment:", frag); continue
        page_schema = None
        if path == "":
            page_schema = home_schema()
        elif path == "pages/real-talk":
            page_schema = books_schema()
        write(path.split("/") if path else [], render(src.read_text(encoding="utf-8"),
              title, desc, SITE + ("/" + path + "/" if path else "/"),
              subnav=path if path in SUBNAV_PAGES else None,
              schema=page_schema))
        urls.append("/" + path + "/" if path else "/")

    # articles
    arts = load_articles()
    live = build_articles(arts)
    build_journal_index(live)
    build_feed(live)
    urls.append(BLOG + "/")
    urls += ["{}/{}/".format(BLOG, a["handle"]) for a in live]

    build_sitemap(urls)

    # Cloudflare Pages redirects (old paths that are NOT being mirrored)
    (DIST / "_redirects").write_text(
        "/pages/start-here            /pages/real-talk        301\n"
        "/pages/real-talk-resources   /pages/free-guides      301\n"
        "/pages/real-talk-starter-pack /pages/free-guides     301\n"
        "/pages/free-resource-library /pages/free-guides      301\n"
        "/pages/shop-all              /pages/real-talk        301\n"
        "/pages/blog                  /blogs/real-talk-articles/  301\n"
        "/collections/books           /pages/real-talk        301\n"
        "/collections/*               /pages/real-talk        301\n"
        "/products/free-coloring-pages-by-ruby-doodle  https://payhip.com/b/EzoB7  301\n"
        "/products/*                  /pages/ruby-doodle      301\n"
        "/pages/dr-scott-fuller       /pages/about-us         301\n"
        "/pages/data-sharing-opt-out  /pages/privacy-policy   301\n"
        "/pages/how-to-use-real-talk-series  /pages/real-talk 301\n"
        "/pages/real-talk-links       /pages/real-talk        301\n"
        "/pages/20-free-coloring-pages-by-ruby-doodle  https://payhip.com/b/EzoB7  301\n"
        "/blogs/walk-talk-down-ivory-road  /blogs/real-talk-articles/  301\n"
        "/blogs/walk-talk-down-ivory-road/*  /blogs/real-talk-articles/  301\n"
        "/pages/faq                   /pages/real-talk        301\n"
        "/pages/floral                /                       301\n"
        "/pages/lifestyle             /                       301\n"
        "/pages/studio-work           /                       301\n"
        "/pages/inspiration           /                       301\n",
        encoding="utf-8")

    n_html = sum(1 for _ in DIST.rglob("index.html"))
    print("Built {} pages ({} live articles) into {}".format(n_html, len(live), DIST))
    queued = [(a["published"], a["handle"]) for a in arts if a["status"] == "scheduled"]
    for d, h in sorted(queued):
        print("  queued for {}: {}".format(d, h))
    drafts = [a["handle"] for a in arts if a["status"] == "draft"]
    if drafts:
        print("  drafts (never published): " + ", ".join(drafts))

if __name__ == "__main__":
    main()

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
FUNNEL  = ROOT / "content" / "funnel"
STATIC = ROOT / "static"
DIST = ROOT / "dist"

SITE = "https://www.ivoryroad.shop"
BLOG = "/blogs/real-talk-articles"

# ---------------------------------------------------------------- funnel
# Standalone Real Talk conversion pages. No site chrome, noindex, not in sitemap.
#
# Cloudflare Web Analytics has no custom events and does not log query strings,
# so the funnel is measured entirely by PAGEVIEWS PER PATH. Every step is its own
# URL. Do not collapse these into one path with UTMs; the UTMs are invisible.
#
#   /rt-ig/ /rt-fb/ ...  landing, one per social ACCOUNT per platform
#   /rt/                 landing, catch-all for email signatures and print
#   /rt/thanks/          signup confirmed (Sender redirects here)
#   /go/amazon/          outbound Amazon click
#
# Sender embedded form.
# Sender renders its forms with their own script, so there is no POST endpoint
# to fill in here. The fields, labels, button text, required flags and the
# post-submit redirect to /rt/thanks/ all live in Sender's form builder.
# Both IDs come from Sender > Forms > Publishing settings.
SENDER_ACCOUNT = "7ecfcf84083377"
SENDER_FORM_ID = "erkw82"

AMAZON_URL    = "https://www.amazon.com/dp/1970494050"
                     # Real Talk student book. The other three are surfaced by
                     # the A+ content on that listing. Plain URL only, never an
                     # Associates tag: Amazon prohibits Special Links in email.
CARDS_URL     = "https://payhip.com/b/DBwq3"
                     # Real Talk Conversation Cards, $7.99. Highest margin thing
                     # in the funnel: we keep nearly all of it, versus a royalty
                     # on the books. Linked from /rt/thanks/ via /go/cards/.

# Sender's loader, copied verbatim from their Publishing settings page and left
# unformatted on purpose: it is full of braces, so it must never go through
# .format(). The account id is swapped in with .replace() at build time.
# This goes on the funnel pages ONLY. Sender tells you to put it on every page;
# there is one form on one page, so site-wide would put a third-party script on
# all 41 pages for no reason and make the privacy page wrong again.
SENDER_SCRIPT = """<!-- Sender form loader. Funnel landings only. -->
<script>
  (function (s, e, n, d, er) {
    s['Sender'] = er;
    s[er] = s[er] || function () {
      (s[er].q = s[er].q || []).push(arguments)
    }, s[er].l = 1 * new Date();
    s[er].on = function(event, callback) {
      s[er].listeners = s[er].listeners || {};
      (s[er].listeners[event] = s[er].listeners[event] || []).push(callback);
    };
    var a = e.createElement(n),
        m = e.getElementsByTagName(n)[0];
    a.async = 1;
    a.src = d;
    m.parentNode.insertBefore(a, m)
  })(window, document, 'script', 'https://cdn.sender.net/accounts_resources/universal.js', 'sender');
  sender('SENDER_ACCOUNT_ID')
</script>"""

# One landing path per BRAND per platform. Same page, different URL. Cloudflare
# does not log query strings, so pageviews on each path ARE the attribution.
#
# Prefix = the brand of the CONTENT the visitor just saw, NOT the account it was
# posted from. On YouTube the link lives in each video's description and on
# Pinterest in each pin, so one account can carry links for several brands. A
# Ruby Doodle video on the @ivoryroadshop channel uses /rd-yt; a Real Talk video
# on that same channel uses /rt-yt. Only TikTok and Instagram collapse brand and
# account into one, because there the link is the bio and there is only one.
#
#   rt Real Talk  |  ir Ivory Road  |  rd Ruby Doodle
#   ig instagram | fb facebook | tt tiktok | pin pinterest | yt youtube
#
# All of these embed the same Sender form, so Sender itself cannot tell them
# apart. Only Cloudflare can, and only by path.
#
# NOT here: Ruby Doodle (/rd-ig /rd-fb /rd-tt /rd-pin /rd-yt). Those must not
# point at this page. The landing page opens with "He says he's fine" and is
# about a teenage son; a coloring book follower is the wrong audience for it.
# Ruby Doodle needs its own destination before any /rd- path is built.
FUNNEL_LANDINGS = [
    "rt",                                          # catch-all: signatures, print, anything unlabelled
    "rt-ig", "rt-fb", "rt-tt", "rt-pin", "rt-yt",  # Real Talk content, wherever it posts from
    "ir-ig", "ir-fb", "ir-tt", "ir-pin", "ir-yt",  # Ivory Road brand content
]

def build_funnel():
    """Write the standalone funnel pages. Deliberately excluded from sitemap.xml."""
    if not FUNNEL.exists():
        print("  !! no content/funnel/, skipping funnel"); return
    missing = [n for n, v in (("SENDER_ACCOUNT", SENDER_ACCOUNT),
                              ("SENDER_FORM_ID", SENDER_FORM_ID),
                              ("AMAZON_URL", AMAZON_URL),
                              ("CARDS_URL", CARDS_URL)) if not v]
    if missing:
        print("  ** funnel: {} still blank in build.py".format(", ".join(missing)))

    loader = SENDER_SCRIPT.replace("SENDER_ACCOUNT_ID", SENDER_ACCOUNT)
    landing = (FUNNEL / "landing.html").read_text(encoding="utf-8")
    for path in FUNNEL_LANDINGS:
        # {{SOURCE}} is the path itself. It ends up in the Sender form's hidden
        # Source field, so the channel is stored on the subscriber rather than
        # only counted as a pageview. See the long comment in landing.html.
        write([path], landing.replace("{{SENDER_SCRIPT}}", loader)
                             .replace("{{SENDER_FORM_ID}}", SENDER_FORM_ID)
                             .replace("{{SOURCE}}", path))

    write(["rt", "thanks"], (FUNNEL / "thanks.html").read_text(encoding="utf-8"))
    write(["go", "amazon"], (FUNNEL / "go-amazon.html")
          .read_text(encoding="utf-8").replace("{{AMAZON_URL}}", AMAZON_URL))
    write(["go", "cards"], (FUNNEL / "go-cards.html")
          .read_text(encoding="utf-8").replace("{{CARDS_URL}}", CARDS_URL))

    print("  funnel: {} landings + /rt/thanks/ + /go/amazon/ + /go/cards/"
          .format(len(FUNNEL_LANDINGS)))

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
    "hidden-signs-teen-boy-insecurity":             "Confidence & Identity",
    "teen-boy-courage-what-fear-looks-like":        "Confidence & Identity",
    "teen-son-feels-different-uniqueness":          "Confidence & Identity",
    "why-teen-boys-wear-masks":                     "Confidence & Identity",
    "what-makes-a-man-what-teen-son-believes":      "Confidence & Identity",
    "what-god-thinks-about-teen-boys":              "Faith",
    "everyday-faith-teen-boys-what-parents-can-do": "Faith",
    "teen-boys-prayer-why-they-go-silent":          "Faith",
    "teen-son-anger-emotional-signals":             "Anger & Emotions",
    "teen-son-replaying-mistakes-shame":            "Anger & Emotions",
    "teen-boy-failure-what-hes-carrying":           "Anger & Emotions",
    "why-teen-boys-blow-up-over-small-things":      "Anger & Emotions",
    "what-to-do-after-teen-son-blowup":             "Anger & Emotions",
    "teen-boy-conflict-whats-really-happening":     "Friends & Relationships",
    "when-teen-son-feels-alone-what-parents-miss":  "Communication",
    "when-teen-son-feels-alone":                    "Communication",
    "stay-connected-teen-son-goes-quiet":           "Communication",
    "small-signs-teen-son-opening-up":              "Communication",
}
# Filter chips on the Articles page, in display order. Written in the language a
# parent uses about the problem, not the language the books use about the chapter.
# "Behind the Series" is deliberately absent: those articles are about Real Talk
# itself, so they stay in All rather than taking a filter slot.
TOPIC_ORDER = ["Communication", "Anger & Emotions", "Confidence & Identity",
               "Friends & Relationships", "Faith"]

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
<!-- Cloudflare Web Analytics. No cookies, no cross-site tracking, no personal data. -->
<script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "c3c701f8454b49b0bb1cb9bfb6cdb28a"}}'></script>
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
    <input id="article-search" class="topic-search" type="search" placeholder="Search anger, friends, confidence, faith..." autocomplete="off">
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

    # funnel (standalone, not added to urls so it stays out of the sitemap)
    build_funnel()

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
        # Hearts and Home welcome sequence, Email 1. Points at the hosted PDF
        # rather than the file directly so the filename can change later
        # without breaking email that has already gone out.
        "/guide                       /static/files/real-talk-hearts-and-home.pdf  301\n"
        "/pages/start-here            /pages/real-talk        301\n"
        "/pages/real-talk-resources   /pages/free-guides      301\n"
        "/pages/real-talk-starter-pack /pages/free-guides     301\n"
        "/pages/free-resource-library /pages/free-guides      301\n"
        "/pages/shop-all              /pages/real-talk        301\n"
        "/pages/blog                  /blogs/real-talk-articles/  301\n"
        "/collections/books           /pages/real-talk        301\n"
        "/collections/*               /pages/real-talk        301\n"
        "/products/free-coloring-pages-by-ruby-doodle  https://payhip.com/b/EzoB7  301\n"
        "/products/the-pickup-truck-a-vintage-collection-of-classic-pickups-digital-pages https://payhip.com/b/E1Bgy 301\n"
        "/products/classic-cars-around-the-world-a-coloring-book-for-classic-car-enthusiasts-digital-pages https://payhip.com/b/7OLIQ 301\n"
        "/products/cozy-country-charm-coloring-book-simple-and-serene-escape-to-peaceful-settings-digital-pages https://payhip.com/b/NM0BG 301\n"
        "/products/winter-fun-a-fun-coloring-and-amazing-activity-book-digital-pages https://payhip.com/b/NbhBd 301\n"
        "/products/tale-of-two-a-celebration-of-unique-friendships-coloring-book-digital-pages https://payhip.com/b/REnX9 301\n"
        "/products/toddlers-animal-coloring-book-fun-and-educational-bilingual-english-spanish-digital-pages-copy https://payhip.com/b/YVZJH 301\n"
        "/products/digital-bundle-the-master-collection-coloring-pages https://payhip.com/b/ME1vx 301\n"
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
        "/pages/inspiration           /                       301\n"
        "/pages/for-youth-pastors /pages/for-leaders 301\n"
        "/blogs/real-talk-articles/when-teen-son-feels-alone  /blogs/real-talk-articles/teen-boy-loneliness-what-god-sees  301\n",
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

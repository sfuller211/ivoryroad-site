# Real Talk Funnel — tracking design and integration

## The constraint you need to know first

**Cloudflare Web Analytics does not support custom events, button-click tracking, goals, or conversion tracking.** Cloudflare's own FAQ answers "Not yet, but we may add support for this in the future." It also does **not log query strings or UTM parameters.**

So the funnel as originally specced (landing page visitors → Free Resources clicks → Amazon clicks as tracked button events) cannot be built on Cloudflare Web Analytics alone. There are no button events to read.

## The workaround: make every funnel step its own URL

Cloudflare Web Analytics counts **pageviews per path**. So instead of tracking clicks, we turn each click into a page load. Every step of the funnel becomes a distinct URL, and the funnel report becomes a list of pageview counts.

| Funnel step | Measured as | Path |
|---|---|---|
| Landing page visit | pageview | `/rt/` (plus per-platform variants below) |
| Guide requested | pageview | `/rt/thanks/` |
| Amazon click | pageview | `/go/amazon/` |
| Real Talk page click | pageview | `/pages/real-talk` |

Read the funnel by comparing pageview counts on those four paths. No custom events, no third-party script, no cookies.

## Source attribution without UTMs

Because Cloudflare does not log query strings, `?utm_source=youtube` tells you nothing. Referrers are also unreliable from social, because in-app browsers on Instagram and TikTok frequently strip or obscure them.

**Fix: give each platform its own landing URL.** Same page, different path.

| Platform | Link in bio / description |
|---|---|
| YouTube | `ivoryroad.shop/yt` |
| TikTok | `ivoryroad.shop/tt` |
| Instagram | `ivoryroad.shop/ig` |
| Pinterest | `ivoryroad.shop/pin` |
| Facebook | `ivoryroad.shop/fb` |
| Everything else | `ivoryroad.shop/rt` |

Pageviews on each path = traffic from that platform. Clean, and it survives referrer stripping.

Build these as copies of the same page, or as redirects into `/rt/` **only if** you accept losing the per-platform count. Copies are better here.

## The redirect timing gotcha

A plain 301/302 redirect never fires the analytics beacon, so an outbound click to Amazon would not be counted. A fast JavaScript redirect has the same problem: the beacon fires on the `load` event, and a redirect can beat it.

`go-amazon.html` handles this. It waits for `window.load`, then waits a further 600ms, then redirects. The visitor sees a brief "Taking you to Amazon" card. That delay is what makes the click countable.

## Amazon links: no Associates tag

Amazon's Associates Operating Agreement prohibits Special Links in email. "Special Links may not be placed in any email publication." Enforcement includes account termination and forfeiture of unpaid commissions.

Use plain Amazon product URLs everywhere in the email sequence. If you ever add an Associates tag, it goes on website pages only, never in an email.

## Files here

| File | What it is |
|---|---|
| `index.html` | The landing page. Standalone, uses the site stylesheet. |
| `go-amazon.html` | Tracked redirect interstitial to Amazon. |
| `EMAILS.md` | The five-email sequence for Sender. |

## Integration steps

1. Copy `index.html` into the build as `/rt/`, then duplicate to `/yt/`, `/tt/`, `/ig/`, `/pin/`, `/fb/`.
2. Copy `go-amazon.html` to `/go/amazon/`. Replace `AMAZON_URL_HERE`.
3. Build a `/rt/thanks/` page. Sender's form settings must redirect there after submit. That redirect is what makes signups countable.
4. Paste your Sender form embed where marked in `index.html`, or point the native form's `action` at the endpoint Sender's embed code gives you. Do not guess the endpoint, copy it from Sender.
5. Enable Cloudflare Web Analytics on the Pages project (one click, free plan).
6. Update every social bio link to the matching per-platform URL.

## What changed from the current site

The live `/pages/free-guides` page offers **three** downloads (Hearts & Home, Real Talk Tools, Ruby Doodle coloring pages) and sends all three to **Payhip**, which is a checkout flow.

This page offers **one** guide, Hearts & Home, with the email field on the page. Reasons:

- Your buyer is parents. Real Talk Tools is for teens and Ruby Doodle is a different brand entirely. Three choices split the intent and dilute the test.
- A checkout step to receive a free PDF is a conversion killer.
- One offer gives you a clean number to measure. Three gives you three small numbers that tell you nothing.

Keep `/pages/free-guides` as it is for site navigation. `/rt/` is the funnel entrance for social traffic, and it does one job.

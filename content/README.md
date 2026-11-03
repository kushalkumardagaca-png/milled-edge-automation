# MILLED EDGE — de-duplication, fresh theme, live heroes (3 November 2026)

## 1 · The mistake, confirmed

Every one of the five pages carried its own copy of the **site shell** inside the page
body: a skip link, a `<header>` with the brand and the seven-item navigation, and a
full `<footer>` with the second identity block, the second inbox line and the share row.
The Blogger theme renders those three things already — which is why readers saw the
identity, the navigation and the footer twice, one above the other.

Measured, before the fix:

| page | page-level `<header>` | page-level `<footer>` | skip link |
|---|---|---|---|
| about-milled-edge | `header.me-site-header` | `footer.me-site-footer` | `a.me-skip` |
| contact-milled-edge | `header.site-header` | `footer.site-footer` | `a.skip` |
| privacy-policy-milled-edge | `header.shell` | `footer.shell` | `a.skip` |
| financial-disclaimer-milled-edge | `header.shell` | `footer.shell` | `a.skip` |
| terms-milled-edge | `header.shell` | `footer.shell` | `a.skip` |

In `pages/*.html` those three elements are gone; the `<main>` content, its styles and its
reveal script remain. Each page still has exactly one `<h1>` and no duplicate shell.

## 2 · The hero: cycling words and a sticky note that stays true

The About page had a cycling hero word and a ledger card that counted live. The other
four pages had a plain title, so they now open the same way — a cycling word in the
cursive face, and a sticky note that is *live*:

| page | cycling words | sticky note shows |
|---|---|---|
| Contact us | hello · namaste · bonjour · salaam | publisher’s local time, live (IST) |
| Privacy policy | your rules · your call · your choice | the reader’s own analytics choice, read from storage |
| Disclaimer | plain sight · broad daylight · black and white | today’s date, live |
| Terms | plain language · short clauses · clear words | the short version of the terms |

The note values marked “live” are written by script when the page opens and refresh
with the reader’s browser state — not hard-coded dates. `prefers-reduced-motion` stops
the cycling and the pulse.

## 3 · Fresh theme file

`theme-milled-edge-fresh.xml` — 460 KB, well-formed, ready to upload by hand at
**Blogger → Theme → Customise → Edit HTML**.

Changes against the theme you sent:

- **Google Analytics 4 added** — `G-DH0BYD3WZG`, the identifier this blog already
  uses. It is **consent-gated**: no request to Google is made until
  `MEGa.grant()` is called (the cookie panel calls it), and `MEGa.deny()` records a
  refusal. Your theme had no GA at all, which is why the tag only appeared on pages.
- **Publisher’s full name throughout** — 17 instances of “Kushal Daga” became
  “Kushal Kumar Daga” (your own rule: the short form is never used).
- Everything else preserved: same widgets, same sections (`header`, `page_list_top`,
  `search_top`, `page_body`, `ads`, `sidebar_feed`, `footer`), same favicon, same
  responsive layout.

**Not in the file:** the word “India” appears nowhere in the theme, and the brand
strings all read `MILLED EDGE`. The domain `millededgeindia.blogspot.com` is
deliberately left alone — that is the address, not the brand.

## 4 · Dead ends

Checked live, all 10 page addresses return **200**; all seven social profiles resolve
(Instagram answered 429 to a scripted request — rate limiting, not a dead link).
Inside the five cleaned pages there are **zero** references to the old domain, **zero**
old-style slugs (`/p/contact-us.html` and friends) and **zero** references to the old
mailbox. The only address now printed is `kushalkumardaga.ca@gmail.com`, which exists.

## 5 · What is live, and what still needs your hands

- **Live now:** nothing from this batch — see the note below.
- **Needs one manual upload:** the theme file. Blogger’s API has no theme-upload
  endpoint, so this one genuinely cannot be automated.
- **Needs the publish lane:** the five cleaned `<main>` blocks, each installed over the
  existing page of the same title so no duplicate pages are created.

# MILLED EDGE content and theme sources

**Checked:** 3 November 2026. The Blogger blog currently has 10 pages and zero public posts; article content is not being published as Blogger posts.

## Theme source—use the right file

- `Milled-Edge-theme-no-daily-news-article.xml` is the no-Daily-News/Article theme source. It is XML-validated and is the file updated in the current task.
- `theme-milled-edge-fresh.xml` is an older alternative. It still contains legacy `kd-articles` and `kd-news` sections and must **not** be uploaded.
- The current task’s theme changes are only in the repository until the publisher uploads the updated XML through Blogger. Do not describe a repository commit as a live theme upload; Blogger’s API workflow does not upload theme XML.

The updated no-Daily theme source:

- keeps the consent-gated GA4 implementation with the confirmed ID `G-DH0BYD3WZG` and removes the duplicate Blogger `google-analytics` include;
- replaces homepage “finance news” metadata with current educational/calculator wording;
- aligns homepage FAQ text and FAQ JSON-LD, uses only the approved desk and publisher emails, and removes unsupported reply-time claims;
- removes the empty footer article-topic archive links and the obsolete label-feed cache/renderer, because the public post feed is intentionally empty;
- keeps the main theme and the 26-desk tool/navigation model intact.

## Page source and publish workflows

- `pages/*.html` contains the five core legal/contact page bodies.
- `pages-fixes/*.html` contains the current ten-page in-place maintenance sources.
- Any commit to `pages-fixes/**` runs `publish-markets-today.yml`, which validates and patches all ten existing pages, not just the changed file. Review all ten sources before triggering it.
- `publish-pages.yml` is a separate lane for the five core pages and uses `content/publish-request.txt` as a push trigger.
- Theme updates require manual Blogger upload; page updates use the Blogger API Actions lane.

## Safety and historical state

- Do not re-enable a destructive workflow trigger without explicit owner direction. The post/page deletion reports are retained in `reports/`; those are historical logs, not current inventories.
- Never commit GitHub Actions secret values, OAuth tokens, `.env` files, or private SSH keys.

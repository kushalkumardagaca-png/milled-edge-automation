# Setup and workflow status

**Checked:** 3 November 2026
**Site:** https://millededgeindia.blogspot.com/
**Repository:** `kushalkumardagaca-png/milled-edge-automation`

## Completed setup

- Blogger API enabled in the owner's Google Cloud project.
- OAuth app branding and client created by the owner.
- GitHub repository created and a write-enabled deploy key added.
- GitHub SSH authentication and a no-op `git push --dry-run` were verified from the agent workspace.
- Workflow run reports confirm the 1 November 2026 cleanup: 654 live posts plus 3 soft-trashed posts were deleted; 0 failures and 0 remaining. The allowlisted Daily News/Daily Article pages were also deleted, leaving 10 pages at that time.

## Current public state

- Current host: `https://millededgeindia.blogspot.com/`.
- Page sitemap: 10 URLs.
- Public post feed and post sitemap: 0 posts, intentionally.
- Robots file points to the current host and its sitemaps.

The repository's inventory and deletion reports are historical snapshots, not a substitute for a fresh read-only inventory before a future publishing batch.

## GitHub Actions credentials

Store these only in repository **Settings → Secrets and variables → Actions**:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

No secret values are stored in this repository. Do not place credentials in a workflow file, report, commit, issue or chat message.

## Workflow state

- `readonly-inventory.yml`: read-only Blogger inventory.
- `publish-pages.yml`: writes the five core pages from `content/pages/`.
- `publish-markets-today.yml`: validates then patches the ten configured existing pages from tracked source files.
- `delete-all-posts.yml` and `delete-two-pages.yml`: destructive jobs. Their trigger files are inactive after the completed cleanup; do not reactivate without explicit owner direction.

The manual theme upload remains a publisher action: Blogger's API publishing workflow does not upload themes. The updated no-Daily source is `content/Milled-Edge-theme-no-daily-news-article.xml`; it is not live until the publisher uploads it in Blogger and public checks confirm it. Do not upload the older `content/theme-milled-edge-fresh.xml` alternative because it contains legacy News/Article sections.

## Audit notes

- The unused `confirm` input was removed from `publish-pages.yml`; the owner’s no-approval workflow now runs on manual dispatch or the publish-request push.
- `publish_pages.py` prevalidates the expected blog ID and all five page destinations before any write. Its local dry-run only checks local bodies and sizes; it is not a remote diff.
- `cleanup_site_pages.py` validates all ten target URLs before patching them, then updates all ten. Any commit to its watched content paths triggers that workflow.

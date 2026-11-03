# MILLED EDGE Automation

Private automation repository for the Blogger site:

- Site: https://millededgeindia.blogspot.com/
- Brand: MILLED EDGE
- Publisher contact: kushalkumardaga.ca@gmail.com
- Blogger blog ID: stored in `config/site.json` (non-secret)

## Current state (3 November 2026)

- The public page sitemap lists 10 pages; public post feed and post sitemap are empty by design.
- The repository's 1 November 2026 Blogger API inventory recorded 654 live posts and 3 soft-trashed posts. The subsequent deletion report records all 657 deleted, zero failures and zero posts remaining. A later read-only check should be run before any new publishing work.
- Page and post writes are possible through GitHub Actions using OAuth values stored only in repository Actions Secrets.
- The no-Daily theme source is `content/Milled-Edge-theme-no-daily-news-article.xml`; the alternate `theme-milled-edge-fresh.xml` is stale and must not be uploaded because it contains legacy News/Article sections. Blogger's API lane does not upload themes. Theme changes still require the publisher to upload the updated no-Daily XML in Blogger.

## Repository layout

```text
config/site.json                  Non-secret site configuration
content/pages/                    Five main page bodies
content/pages-fixes/              Current in-place page bodies for maintenance
content/Milled-Edge-theme-no-daily-news-article.xml  No-Daily theme source; manual upload required
scripts/                           Blogger API helpers and maintenance scripts
.github/workflows/                 Read-only, page-write and guarded deletion workflows
trigger/                           Inactive confirmation files for destructive workflows
reports/                           Historical workflow reports; not a live inventory
```

## Available workflows

- `readonly-inventory.yml`: reads Blogger pages/posts and writes a timestamped report.
- `publish-pages.yml`: updates the five existing core pages when `content/publish-request.txt` changes or the workflow is manually dispatched. It runs a local dry-run preflight, then performs the API write.
- `publish-markets-today.yml`: validates and patches ten existing pages in place when tracked page-fix sources change.
- `delete-two-pages.yml` and `delete-all-posts.yml`: destructive jobs with explicit confirmation-file guards. Their trigger files currently say `INACTIVE`. Do not activate them unless the publisher explicitly directs a new deletion.

Before changing a write workflow, inspect its matching rules, conditions, page scope and failure behavior. The `publish-pages.yml` dispatch input currently does not gate the job; the script's hard-coded confirmation is what authorizes the write. The dry-run reports local file sizes and is not a remote content diff. Do not treat either as proof that live Blogger content matches the repository.

## Secrets and access

The following values belong only in repository **Settings → Secrets and variables → Actions**:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Never commit secret values, OAuth tokens, private keys or `.env` files. The SSH deploy-key private half stays outside the repository. Do not paste it into chat. No key values belong in this README.

# MILLED EDGE Automation

Private automation repository for transforming the existing Blogger website:

- Website: https://millededgeindia.blogspot.com/
- Brand: MILLED EDGE
- Author contact: kushalkumardaga.ca@gmail.com

## Current phase

**Read-only setup and inventory only.**

This repository does not yet contain workflows that delete posts, delete pages, publish content, or modify the live Blogger theme.

## Safety rules

1. Never commit secrets, OAuth tokens, private keys, or `.env` files.
2. Store credentials only in GitHub Actions Secrets.
3. Run read-only inventory before any write operation.
4. Create a backup before destructive changes.
5. Destructive workflows must be added later as separate, explicitly approved jobs.

## Repository layout

```text
config/site.json              Non-secret website configuration
scripts/blogger_client.py     Shared Blogger API client helpers
scripts/readonly_inventory.py Read-only inventory script
.github/workflows/            GitHub Actions workflows
```

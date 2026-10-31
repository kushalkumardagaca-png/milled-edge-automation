# Setup status

## Completed

- Existing Blogger website identified: https://millededgeindia.blogspot.com/
- Google Cloud project created by owner.
- Blogger API enabled.
- OAuth app branding completed and app published.
- OAuth client created.
- GitHub repository created.
- Repository deploy key added with write access.

## Current repository phase

Read-only inventory.

## Required GitHub Actions Secrets

Add these in repository Settings → Secrets and variables → Actions:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

Do not commit these values to the repository.

## Not enabled yet

- Post deletion
- Page deletion
- Page creation/update
- Theme changes
- Automated publishing

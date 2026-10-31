"""Shared read-only-safe Blogger API client helpers.

This module does not perform write operations by itself.
Credentials must come from environment variables, never from committed files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BLOGGER_SCOPES = ["https://www.googleapis.com/auth/blogger"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
ROOT = Path(__file__).resolve().parent.parent


def load_site_config() -> dict[str, Any]:
    config_path = ROOT / "config" / "site.json"
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_credentials() -> Credentials:
    credentials = Credentials(
        token=None,
        refresh_token=require_env("GOOGLE_REFRESH_TOKEN"),
        token_uri=TOKEN_URI,
        client_id=require_env("GOOGLE_CLIENT_ID"),
        client_secret=require_env("GOOGLE_CLIENT_SECRET"),
        scopes=BLOGGER_SCOPES,
    )
    credentials.refresh(Request())
    return credentials


def get_blogger_service():
    return build("blogger", "v3", credentials=get_credentials(), cache_discovery=False)


def get_blog_by_url(service, blog_url: str) -> dict[str, Any]:
    return service.blogs().getByUrl(url=blog_url).execute()

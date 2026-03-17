
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_resume() -> str:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    # auto-refreshes using the refresh token
    creds.refresh(Request())

    service = build("docs", "v1", credentials=creds, cache_discovery=False)
    doc = service.documents().get(documentId=os.environ["RESUME_DOC_ID"]).execute()
    return _extract_text(doc)

def _extract_text(doc: dict) -> str:
    parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for elem in paragraph.get("elements", []):
            text_run = elem.get("textRun")
            if text_run:
                parts.append(text_run.get("content", ""))
    return "".join(parts).strip()

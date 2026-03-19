import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def _get_creds() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return creds


def get_resume() -> str:
    creds = _get_creds()
    service = build("docs", "v1", credentials=creds, cache_discovery=False)
    doc = service.documents().get(documentId=os.environ["RESUME_DOC_ID"]).execute()
    return _extract_text(doc)


def get_resume_modified_time() -> str:
    creds = _get_creds()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = service.files().get(
        fileId=os.environ["RESUME_DOC_ID"],
        fields="modifiedTime",
    ).execute()
    return meta["modifiedTime"]  # ISO 8601 Format


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

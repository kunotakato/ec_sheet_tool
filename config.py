from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    rakuten_application_id: str
    rakuten_access_key: str
    spreadsheet_id: str
    google_credentials_file: str
    google_token_file: str
    settings_sheet_name: str
    raw_data_sheet_name: str
    request_timeout: int


def get_settings() -> Settings:
    settings = Settings(
        rakuten_application_id=os.getenv("RAKUTEN_APPLICATION_ID", "").strip(),
        rakuten_access_key=os.getenv("RAKUTEN_ACCESS_KEY", "").strip(),
        spreadsheet_id=os.getenv("SPREADSHEET_ID", "").strip(),
        google_credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip(),
        google_token_file=os.getenv("GOOGLE_TOKEN_FILE", "token.json").strip(),
        settings_sheet_name=os.getenv("SETTINGS_SHEET_NAME", "settings").strip(),
        raw_data_sheet_name=os.getenv("RAW_DATA_SHEET_NAME", "raw_data").strip(),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT") or "20"),
    )

    missing = []
    if not settings.rakuten_application_id:
        missing.append("RAKUTEN_APPLICATION_ID")
    if not settings.rakuten_access_key:
        missing.append("RAKUTEN_ACCESS_KEY")
    if not settings.spreadsheet_id:
        missing.append("SPREADSHEET_ID")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f".env に未設定の項目があります: {joined}")

    return settings
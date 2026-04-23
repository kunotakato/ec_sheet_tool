from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class FetchAndSaveSettings:
    rakuten_application_id: str
    rakuten_access_key: str
    request_timeout: int
    spreadsheet_id: str
    raw_data_sheet_name: str
    google_service_account_json: str


def get_fetch_and_save_settings() -> FetchAndSaveSettings:
    rakuten_application_id = (os.getenv("RAKUTEN_APPLICATION_ID") or "").strip()
    rakuten_access_key = (os.getenv("RAKUTEN_ACCESS_KEY") or "").strip()
    spreadsheet_id = (os.getenv("SPREADSHEET_ID") or "").strip()
    raw_data_sheet_name = (os.getenv("RAW_DATA_SHEET_NAME") or "raw_data").strip() or "raw_data"
    google_service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or ""

    missing: list[str] = []

    if not rakuten_application_id:
        missing.append("RAKUTEN_APPLICATION_ID")
    if not rakuten_access_key:
        missing.append("RAKUTEN_ACCESS_KEY")
    if not spreadsheet_id:
        missing.append("SPREADSHEET_ID")
    if not google_service_account_json.strip():
        missing.append("GOOGLE_SERVICE_ACCOUNT_JSON")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f".env に未設定の項目があります: {joined}")

    try:
        request_timeout = int(os.getenv("REQUEST_TIMEOUT") or "20")
    except ValueError as e:
        raise ValueError("REQUEST_TIMEOUT は数値で設定してください。例: 20") from e

    return FetchAndSaveSettings(
        rakuten_application_id=rakuten_application_id,
        rakuten_access_key=rakuten_access_key,
        request_timeout=request_timeout,
        spreadsheet_id=spreadsheet_id,
        raw_data_sheet_name=raw_data_sheet_name,
        google_service_account_json=google_service_account_json,
    )
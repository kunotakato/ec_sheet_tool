from __future__ import annotations

import os.path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_google_credentials(credentials_file: str, token_file: str) -> Credentials:
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


class SheetsClient:
    def __init__(self, spreadsheet_id: str, credentials_file: str, token_file: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        creds = get_google_credentials(credentials_file, token_file)
        self.service = build("sheets", "v4", credentials=creds)

    def append_row(self, sheet_name: str, row: list[Any]) -> dict[str, Any]:
        body = {"values": [row]}
        result = (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        return result

    def append_rows(self, sheet_name: str, rows: list[list[Any]]) -> dict[str, Any]:
        if not rows:
            return {}

        body = {"values": rows}
        result = (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        return result

    def get_active_keywords(self, sheet_name: str) -> list[str]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A2:B",
            )
            .execute()
        )

        rows = result.get("values", [])
        keywords: list[str] = []

        for row in rows:
            keyword = row[0].strip() if len(row) >= 1 else ""
            is_active_raw = row[1].strip().lower() if len(row) >= 2 else "true"

            is_active = is_active_raw in {"true", "1", "yes", "y", "on"}
            if keyword and is_active:
                keywords.append(keyword)

        return keywords

    def get_latest_item_states(self, sheet_name: str) -> dict[str, dict[str, str]]:
        """
        raw_data シートから、item_code ごとの最新状態を返します。

        返す内容:
        {
            "item_code": {
                "fetched_at": "...",
                "item_price": "...",
                "availability": "..."
            }
        }
        """
        result = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A2:H",
            )
            .execute()
        )

        rows = result.get("values", [])
        latest_states: dict[str, dict[str, str]] = {}

        for row in rows:
            fetched_at = row[0].strip() if len(row) > 0 else ""
            item_price = row[3].strip() if len(row) > 3 else ""
            availability = row[4].strip() if len(row) > 4 else ""
            item_code = row[7].strip() if len(row) > 7 else ""

            if not item_code:
                continue

            current = latest_states.get(item_code)

            # fetched_at は ISO形式で入れている前提なので、文字列比較で新旧判定できる
            if current is None or fetched_at > current["fetched_at"]:
                latest_states[item_code] = {
                    "fetched_at": fetched_at,
                    "item_price": item_price,
                    "availability": availability,
                }

        return latest_states
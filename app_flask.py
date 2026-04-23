from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests
from flask import Flask, jsonify, request  # pyright: ignore[reportMissingImports]
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import get_fetch_and_save_settings

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_service(google_service_account_json: str):
    service_account_info = json.loads(google_service_account_json)
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=credentials)
    return service


def fetch_rakuten_items(settings, keyword: str) -> tuple[int, dict[str, Any]]:
    endpoint = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"

    origin = request.host_url.rstrip("/")
    referer = request.host_url

    params = {
        "applicationId": settings.rakuten_application_id,
        "accessKey": settings.rakuten_access_key,
        "keyword": keyword,
        "hits": 1,
        "format": "json",
        "formatVersion": 2,
        "availability": 0,
        "elements": "itemName,itemPrice,availability,itemUrl,shopName,itemCode",
    }

    headers = {
        "Origin": origin,
        "Referer": referer,
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(
        endpoint,
        params=params,
        headers=headers,
        timeout=settings.request_timeout,
    )

    try:
        response_json = response.json()
    except ValueError:
        response_json = {"raw_text": response.text[:1000]}

    return response.status_code, response_json


def extract_items(response_json: dict[str, Any]) -> list[dict[str, Any]]:
    items = response_json.get("items") or response_json.get("Items") or []
    if not isinstance(items, list):
        return []
    return items


def build_row(keyword: str, item: dict[str, Any]) -> list[Any]:
    fetched_at = datetime.now(timezone.utc).isoformat()

    return [
        fetched_at,
        keyword,
        item.get("itemName", ""),
        item.get("itemPrice", ""),
        item.get("availability", ""),
        item.get("itemUrl", ""),
        item.get("shopName", ""),
        item.get("itemCode", ""),
    ]


def append_row_to_sheet(settings, row: list[Any]) -> dict[str, Any]:
    service = get_sheets_service(settings.google_service_account_json)

    body = {"values": [row]}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=settings.spreadsheet_id,
            range=f"{settings.raw_data_sheet_name}!A:A",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    return result


@app.route("/")
def index():
    return {
        "message": "Rakuten Flask app is running on Render.",
        "usage_fetch": "/fetch?keyword=ワイヤレスイヤホン",
        "usage_fetch_and_save": "/fetch-and-save?keyword=ワイヤレスイヤホン",
    }


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/fetch")
def fetch_items():
    try:
        settings = get_fetch_and_save_settings()

        keyword = request.args.get("keyword", "").strip()
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400

        status_code, response_json = fetch_rakuten_items(settings, keyword)

        return jsonify({
            "status_code": status_code,
            "sent_headers": {
                "Origin": request.host_url.rstrip("/"),
                "Referer": request.host_url,
            },
            "response_json": response_json,
        }), status_code

    except Exception as e:
        app.logger.exception("Exception on /fetch")
        return jsonify({
            "error": "internal_server_error",
            "detail": str(e),
        }), 500


@app.route("/fetch-and-save")
def fetch_and_save():
    try:
        settings = get_fetch_and_save_settings()

        keyword = request.args.get("keyword", "").strip()
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400

        status_code, response_json = fetch_rakuten_items(settings, keyword)

        if status_code != 200:
            return jsonify({
                "status_code": status_code,
                "sent_headers": {
                    "Origin": request.host_url.rstrip("/"),
                    "Referer": request.host_url,
                },
                "response_json": response_json,
            }), status_code

        items = extract_items(response_json)
        if not items:
            return jsonify({
                "error": "no_items_found",
                "detail": "楽天APIのレスポンスに items / Items がありませんでした。",
                "response_json": response_json,
            }), 404

        item = items[0]
        row = build_row(keyword, item)
        append_result = append_row_to_sheet(settings, row)

        return jsonify({
            "message": "fetch and save succeeded",
            "saved_row": {
                "fetched_at": row[0],
                "keyword": row[1],
                "item_name": row[2],
                "item_price": row[3],
                "availability": row[4],
                "item_url": row[5],
                "shop_name": row[6],
                "item_code": row[7],
            },
            "append_result": append_result,
        }), 200

    except Exception as e:
        app.logger.exception("Exception on /fetch-and-save")
        return jsonify({
            "error": "internal_server_error",
            "detail": str(e),
        }), 500
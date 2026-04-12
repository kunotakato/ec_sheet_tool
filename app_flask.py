from __future__ import annotations
import os

import requests
from flask import Flask, jsonify, request  # pyright: ignore[reportMissingImports]
from config import get_fetch_settings

app = Flask(__name__)


@app.route("/")
def index():
    return {
        "message": "Rakuten Flask app is running on Render.",
        "usage": "/fetch?keyword=ワイヤレスイヤホン"
    }


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/fetch")
def fetch_items():
    try:
        settings = get_fetch_settings()  # pyright: ignore[reportUndefinedVariable]

        keyword = request.args.get("keyword", "").strip()
        if not keyword:
            return jsonify({"error": "keyword is required"}), 400

        endpoint = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"

        params = {
            "applicationId": settings.rakuten_application_id,
            "keyword": keyword,
            "hits": 1,
            "format": "json",
            "formatVersion": 2,
            "availability": 0,
            "elements": "itemName,itemPrice,availability,itemUrl,shopName,itemCode",
        }

        headers = {
            "accessKey": settings.rakuten_access_key,
            "Referer": request.host_url,
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

        return jsonify({
            "status_code": response.status_code,
            "sent_headers": {
                "Referer": request.host_url,
                "accessKey": "***masked***",
            },
            "response_json": response_json,
        }), response.status_code

    except Exception as e:
        app.logger.exception("Exception on /fetch")
        return jsonify({
            "error": "internal_server_error",
            "detail": str(e)
        }), 500
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
from __future__ import annotations

import requests
from flask import Flask, jsonify, request  # pyright: ignore[reportMissingImports]

from config import get_settings

app = Flask(__name__)


@app.route("/")
def index():
    return {
        "message": "Rakuten Flask minimal app is running.",
        "usage": "/fetch?keyword=ワイヤレスイヤホン"
    }


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/fetch")
def fetch_items():
    settings = get_settings()

    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"error": "keyword is required"}), 400

    endpoint = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"

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

    try:
        response = requests.get(endpoint, params=params, timeout=settings.request_timeout)

        return jsonify({
            "status_code": response.status_code,
            "request_url": response.url,
            "response_json": response.json()
        }), response.status_code

    except requests.RequestException as e:
        return jsonify({
            "error": "request failed",
            "detail": str(e)
        }), 500

    except ValueError:
        return jsonify({
            "error": "response is not valid json",
            "response_text": response.text
        }), response.status_code if "response" in locals() else 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
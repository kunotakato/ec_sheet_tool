from __future__ import annotations

from config import get_settings
from normalizer import normalize_item
from rakuten_client import RakutenClient
from sheets_client import SheetsClient


def main() -> None:
    settings = get_settings()

    sheets = SheetsClient(
        spreadsheet_id=settings.spreadsheet_id,
        credentials_file=settings.google_credentials_file,
        token_file=settings.google_token_file,
    )

    client = RakutenClient(
        application_id=settings.rakuten_application_id,
        access_key=settings.rakuten_access_key,
        timeout=settings.request_timeout,
    )

    keywords = sheets.get_active_keywords(settings.settings_sheet_name)
    if not keywords:
        print("settings シートに有効な keyword がありません。")
        return

    latest_item_states = sheets.get_latest_item_states(settings.raw_data_sheet_name)
    print(f"[INFO] 既存の最新 item_code 状態を {len(latest_item_states)} 件読み込みました。")

    all_rows: list[list] = []
    skipped_count = 0
    added_count = 0

    for keyword in keywords:
        try:
            items = client.search_items(keyword=keyword, hits=5)

            if not items:
                print(f"[INFO] '{keyword}' に一致する商品はJSON内にありませんでした。")
                continue

            added_for_keyword = 0

            for item in items:
                row = normalize_item(keyword, item)

                # row の構成
                # 0: fetched_at
                # 1: keyword
                # 2: item_name
                # 3: item_price
                # 4: availability
                # 5: item_url
                # 6: shop_name
                # 7: item_code

                item_price = str(row[3]).strip()
                availability = str(row[4]).strip()
                item_code = str(row[7]).strip()

                if not item_code:
                    print("[WARN] item_code が空のため、そのまま追加します。")
                    all_rows.append(row)
                    added_for_keyword += 1
                    added_count += 1
                    continue

                latest = latest_item_states.get(item_code)

                # まだ一度も保存されていなければ追加
                if latest is None:
                    all_rows.append(row)
                    latest_item_states[item_code] = {
                        "fetched_at": str(row[0]),
                        "item_price": item_price,
                        "availability": availability,
                    }
                    added_for_keyword += 1
                    added_count += 1
                    continue

                # 価格・在庫が前回と同じならスキップ
                same_price = latest["item_price"] == item_price
                same_availability = latest["availability"] == availability

                if same_price and same_availability:
                    skipped_count += 1
                    print(f"[SKIP] 価格・在庫に変化なし: {item_code}")
                    continue

                # 価格または在庫が変わったので履歴として追加
                all_rows.append(row)
                latest_item_states[item_code] = {
                    "fetched_at": str(row[0]),
                    "item_price": item_price,
                    "availability": availability,
                }
                added_for_keyword += 1
                added_count += 1
                print(f"[ADD] 履歴追加（価格または在庫変化）: {item_code}")

            print(f"[INFO] '{keyword}' から {added_for_keyword} 件を追加対象にしました。")

        except Exception as e:
            print(f"[ERROR] '{keyword}' の取得で失敗しました: {e}")

    if not all_rows:
        print("追加する新規履歴データがありませんでした。")
        print(f"[INFO] スキップ件数: {skipped_count}")
        return

    sheets.append_rows(settings.raw_data_sheet_name, all_rows)
    print(f"raw_data シートに {len(all_rows)} 行を追加しました。")
    print(f"[INFO] 追加件数: {added_count}")
    print(f"[INFO] スキップ件数: {skipped_count}")


if __name__ == "__main__":
    main()
    from __future__ import annotations

import os
import requests
from flask import Flask, jsonify, request  # pyright: ignore[reportMissingImports]
from config import get_settings

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

    response = requests.get(endpoint, params=params, timeout=settings.request_timeout)

    return jsonify({
        "status_code": response.status_code,
        "request_url": response.url,
        "response_json": response.json()
    }), response.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
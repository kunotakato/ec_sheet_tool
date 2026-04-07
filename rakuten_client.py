from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


class RakutenClient:
    """
    dataフォルダ内の複数JSONを読み込む簡易版クライアント。
    """

    def __init__(self, application_id: str = "", access_key: str = "", timeout: int = 20) -> None:
        self.application_id = application_id
        self.access_key = access_key
        self.timeout = timeout
        self.data_dir = Path("data")

    def _load_all_items(self) -> list[dict[str, Any]]:
        if not self.data_dir.exists():
            raise FileNotFoundError(f"dataフォルダが見つかりません: {self.data_dir}")

        json_files = sorted(self.data_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"dataフォルダ内にJSONファイルがありません: {self.data_dir}")

        all_items: list[dict[str, Any]] = []

        for json_file in json_files:
            try:
                text = json_file.read_text(encoding="utf-8-sig").strip()

                if not text:
                    print(f"[WARN] {json_file.name} は空ファイルのためスキップします。")
                    continue

                data = json.loads(text)

                items = data.get("items") or data.get("Items") or []

                if not isinstance(items, list):
                    print(f"[WARN] {json_file.name} の items / Items が配列ではないためスキップします。")
                    continue

                for item in items:
                    all_items.append(item)

            except JSONDecodeError as e:
                print(f"[WARN] {json_file.name} はJSONとして壊れています: {e}")
                continue

        return all_items

    def search_items(self, keyword: str, hits: int = 5) -> list[dict[str, Any]]:
        all_items = self._load_all_items()

        matched_items: list[dict[str, Any]] = []
        seen_item_codes: set[str] = set()

        for item in all_items:
            item_name = item.get("itemName", "")
            item_code = item.get("itemCode", "")

            if keyword not in item_name:
                continue

            if item_code and item_code in seen_item_codes:
                continue

            normalized_item = {
                "itemName": item.get("itemName", ""),
                "itemPrice": item.get("itemPrice", 0),
                "availability": item.get("availability", 0),
                "itemUrl": item.get("itemUrl", ""),
                "shopName": item.get("shopName", ""),
                "itemCode": item.get("itemCode", ""),
            }

            matched_items.append(normalized_item)

            if item_code:
                seen_item_codes.add(item_code)

            if len(matched_items) >= hits:
                break

        return matched_items
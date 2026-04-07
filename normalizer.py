from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

JST = timezone(timedelta(hours=9))


def availability_to_text(value: Any) -> str:
    return "在庫あり" if str(value) == "1" else "在庫なし"


def normalize_item(keyword: str, item: dict[str, Any]) -> list[Any]:
    return [
        datetime.now(JST).isoformat(timespec="seconds"),
        keyword,
        item.get("itemName", ""),
        item.get("itemPrice", ""),
        availability_to_text(item.get("availability", "")),
        item.get("itemUrl", ""),
        item.get("shopName", ""),
        item.get("itemCode", ""),
    ]
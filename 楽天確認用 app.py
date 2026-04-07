from config import get_settings
from rakuten_client import RakutenClient


def main() -> None:
    settings = get_settings()

    rakuten = RakutenClient(
        application_id=settings.rakuten_application_id,
        access_key=settings.rakuten_access_key,
        timeout=settings.request_timeout,
    )

    items = rakuten.search_items("ワイヤレスイヤホン", hits=1)

    if not items:
        print("商品が取得できませんでした。")
        return

    first = items[0]
    print("1件取得できました。")
    print(first)


if __name__ == "__main__":
    main()
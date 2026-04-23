from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class FetchSettings:
    rakuten_application_id: str
    rakuten_access_key: str
    request_timeout: int

def get_fetch_settings() -> FetchSettings:
    app_id = (os.getenv("RAKUTEN_APPLICATION_ID") or "").strip()
    access_key = (os.getenv("RAKUTEN_ACCESS_KEY") or "").strip()
    request_timeout = int(os.getenv("REQUEST_TIMEOUT") or "20")

    missing = []
    if not app_id:
        missing.append("RAKUTEN_APPLICATION_ID")
    if not access_key:
        missing.append("RAKUTEN_ACCESS_KEY")

    if missing:
        raise ValueError(f".env に未設定の項目があります: {', '.join(missing)}")

    return FetchSettings(
        rakuten_application_id=app_id,
        rakuten_access_key=access_key,
        request_timeout=request_timeout,
    )
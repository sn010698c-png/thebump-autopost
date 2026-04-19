"""
refresh_token.py - Tự động làm mới Facebook Page Token

Flow:
  User Token (1h) → Long-lived User Token (60 ngày) → Page Token (không hết hạn)

Chạy thủ công:
  PYTHONUTF8=1 python refresh_token.py

Tự động: được gọi từ main.py khi token sắp hết hạn (còn < 7 ngày)
"""
import os
import re
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".env"
FB_API   = "https://graph.facebook.com/v19.0"


def _read_env() -> dict:
    load_dotenv(ENV_FILE, override=True)
    return {
        "app_id":      os.environ.get("FB_APP_ID", ""),
        "app_secret":  os.environ.get("FB_APP_SECRET", ""),
        "user_token":  os.environ.get("FB_USER_TOKEN", ""),
        "page_token":  os.environ.get("FB_PAGE_TOKEN", ""),
        "page_id":     os.environ.get("FB_PAGE_ID", ""),
    }


def _update_env(key: str, value: str):
    content = ENV_FILE.read_text(encoding="utf-8")
    pattern = rf"^{key}=.*"
    replacement = f"{key}={value}"
    if re.search(pattern, content, flags=re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{key}={value}"
    ENV_FILE.write_text(content, encoding="utf-8")


def get_token_expiry(token: str) -> datetime | None:
    """Kiểm tra token còn hạn đến khi nào."""
    env = _read_env()
    # Dùng app token để debug (app_id|app_secret)
    app_token = f"{env['app_id']}|{env['app_secret']}" if env["app_id"] else token
    r = requests.get(f"{FB_API}/debug_token", params={
        "input_token": token,
        "access_token": app_token,
    }, timeout=10)
    data = r.json().get("data", {})
    expires_at = data.get("expires_at", 0)
    if expires_at == 0:
        return None  # token không hết hạn (Page Token lâu dài)
    return datetime.fromtimestamp(expires_at, tz=timezone.utc)


def exchange_long_lived_token(short_token: str) -> str:
    """Đổi short-lived User Token → long-lived User Token (60 ngày)."""
    env = _read_env()
    if not env["app_id"] or not env["app_secret"]:
        raise ValueError("Thiếu FB_APP_ID hoặc FB_APP_SECRET trong .env")

    r = requests.get(f"{FB_API}/oauth/access_token", params={
        "grant_type":        "fb_exchange_token",
        "client_id":         env["app_id"],
        "client_secret":     env["app_secret"],
        "fb_exchange_token": short_token,
    }, timeout=10)
    result = r.json()
    if "error" in result:
        raise RuntimeError(f"Lỗi exchange token: {result['error']['message']}")
    return result["access_token"]


def get_page_token_from_user_token(user_token: str, page_id: str) -> str:
    """Lấy Page Token từ User Token."""
    r = requests.get(f"{FB_API}/me/accounts", params={"access_token": user_token}, timeout=10)
    for page in r.json().get("data", []):
        if page["id"] == page_id:
            return page["access_token"]
    raise RuntimeError(f"Không tìm thấy Page ID {page_id} trong danh sách pages.")


def refresh(new_user_token: str = None) -> bool:
    """
    Làm mới token. Trả về True nếu thành công.
    - Nếu truyền new_user_token: dùng token đó để exchange.
    - Nếu không: dùng FB_USER_TOKEN trong .env để refresh.
    """
    env = _read_env()

    token_to_exchange = new_user_token or env["user_token"]
    if not token_to_exchange:
        print("Không có User Token để refresh. Cần nhập token mới.")
        return False

    print("Đang exchange long-lived User Token...")
    long_lived = exchange_long_lived_token(token_to_exchange)
    _update_env("FB_USER_TOKEN", long_lived)
    print("Long-lived User Token đã lưu.")

    print("Đang lấy Page Token...")
    page_token = get_page_token_from_user_token(long_lived, env["page_id"])
    _update_env("FB_PAGE_TOKEN", page_token)
    print("Page Token đã cập nhật vào .env.")

    return True


def should_refresh() -> bool:
    """Kiểm tra xem Page Token có cần refresh không (hết hạn hoặc còn < 7 ngày)."""
    env = _read_env()
    if not env["page_token"]:
        return True
    expiry = get_token_expiry(env["page_token"])
    if expiry is None:
        return False  # Page Token không hết hạn → không cần refresh
    days_left = (expiry - datetime.now(tz=timezone.utc)).days
    print(f"Token còn hạn: {days_left} ngày")
    return days_left < 7


if __name__ == "__main__":
    env = _read_env()

    if not env["app_id"] or not env["app_secret"]:
        print("Lỗi: Cần điền FB_APP_ID và FB_APP_SECRET vào .env trước.")
        print("Lấy tại: developers.facebook.com → App của mày → App Settings → Basic")
        sys.exit(1)

    # Nhận token từ argument hoặc stdin
    if len(sys.argv) > 1:
        new_token = sys.argv[1].strip()
    else:
        print("Nhập User Token mới từ Graph API Explorer:")
        new_token = input("Token: ").strip()

    if not new_token:
        print("Không có token. Thoát.")
        sys.exit(1)

    if refresh(new_token):
        print("\nHoàn thành! Token đã được làm mới và lưu vào .env")
    else:
        print("\nThất bại.")
        sys.exit(1)

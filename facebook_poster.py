"""
facebook_poster.py - Đăng bài lên Facebook Page qua Graph API
"""
import os
import io
import requests
from dotenv import load_dotenv

load_dotenv()

FB_API_VERSION = "v19.0"
FB_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"


def _get_credentials() -> tuple[str, str]:
    token = os.environ.get("FB_PAGE_TOKEN", "")
    page_id = os.environ.get("FB_PAGE_ID", "")
    if not token or not page_id:
        raise ValueError("Thiếu FB_PAGE_TOKEN hoặc FB_PAGE_ID trong .env")
    return token, page_id


def post_photo_with_caption(image_bytes: bytes, caption: str) -> dict:
    """Đăng ảnh + caption lên Facebook Page — hiện trên timeline public.
    Flow: upload ảnh unpublished → lấy photo_id → post feed với attached_media.
    """
    token, page_id = _get_credentials()

    # Bước 1: Upload ảnh unpublished → lấy photo_id
    r1 = requests.post(
        f"{FB_BASE_URL}/{page_id}/photos",
        files={"source": ("image.png", io.BytesIO(image_bytes), "image/png")},
        data={"access_token": token, "published": "false"},
        timeout=60,
    )
    result1 = r1.json()
    if r1.status_code != 200 or "error" in result1:
        raise RuntimeError(f"Upload ảnh lỗi: {result1}")
    photo_id = result1["id"]
    print(f"  Uploaded photo_id: {photo_id}")

    # Bước 2: Post lên /feed với ảnh đính kèm → xuất hiện trên timeline
    import json as _json
    r2 = requests.post(
        f"{FB_BASE_URL}/{page_id}/feed",
        data={
            "message": caption,
            "attached_media": _json.dumps([{"media_fbid": photo_id}]),
            "access_token": token,
        },
        timeout=30,
    )
    result2 = r2.json()
    if r2.status_code != 200 or "error" in result2:
        raise RuntimeError(f"Đăng feed lỗi: {result2}")

    print(f"  Đã đăng lên Facebook! Post ID: {result2.get('id')}")
    return result2


def post_text_only(caption: str) -> dict:
    """Đăng text-only khi không có ảnh."""
    token, page_id = _get_credentials()

    url = f"{FB_BASE_URL}/{page_id}/feed"
    data = {
        "message": caption,
        "access_token": token,
    }

    response = requests.post(url, data=data, timeout=30)
    result = response.json()

    if response.status_code != 200 or "error" in result:
        raise RuntimeError(f"Facebook API lỗi: {result}")

    print(f"  Đã đăng text lên Facebook! Post ID: {result.get('id')}")
    return result


def post_article(processed_article: dict) -> dict:
    """Đăng 1 bài (ảnh + caption hoặc text-only) lên Facebook Page."""
    caption = processed_article["caption"]
    image_bytes = processed_article.get("image_bytes")

    if image_bytes:
        return post_photo_with_caption(image_bytes, caption)
    else:
        return post_text_only(caption)


def verify_token() -> bool:
    """Kiểm tra Page Access Token còn hợp lệ không."""
    token, page_id = _get_credentials()
    url = f"{FB_BASE_URL}/{page_id}"
    params = {"fields": "name,id", "access_token": token}
    response = requests.get(url, params=params, timeout=15)
    result = response.json()

    if "error" in result:
        print(f"  Token không hợp lệ: {result['error']['message']}")
        return False

    print(f"  Token OK - Page: {result.get('name')} (ID: {result.get('id')})")
    return True


if __name__ == "__main__":
    print("Kiểm tra Facebook token...")
    if verify_token():
        print("Token hợp lệ! Sẵn sàng đăng bài.")
    else:
        print("Token lỗi. Vui lòng kiểm tra lại .env")

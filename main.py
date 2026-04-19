"""
main.py - Orchestrator: scrape → AI xử lý → đăng Facebook
Chạy mỗi ngày 1 lần qua Windows Task Scheduler
"""
import asyncio
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from scraper import get_new_articles, save_posted_url
from ai_processor import process_article
from facebook_poster import post_article, verify_token
from refresh_token import should_refresh, refresh

BASE_DIR   = Path(__file__).parent
LOG_FILE   = BASE_DIR / "logs" / "run.log"
IMAGES_DIR = BASE_DIR / "images"


def log(msg: str):
    LOG_FILE.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_image(image_bytes: bytes, title: str) -> Path:
    """Lưu ảnh vào images/YYYY-MM-DD/ với tên theo tiêu đề bài."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder = IMAGES_DIR / date_str
    folder.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r"[^\w\s-]", "", title).strip()
    safe_title = re.sub(r"\s+", "_", safe_title)[:60]
    timestamp  = datetime.now().strftime("%H%M%S")
    filepath   = folder / f"{timestamp}_{safe_title}.png"
    filepath.write_bytes(image_bytes)
    return filepath


async def run():
    log("=" * 50)
    log("Bắt đầu chạy thebump-autopost")

    # 1. Kiểm tra và tự động làm mới Facebook token nếu cần
    log("Kiểm tra Facebook token...")
    if should_refresh():
        log("Token sắp hết hạn hoặc chưa có. Đang tự động làm mới...")
        if not refresh():
            log("LỖI: Không thể tự refresh token. Cần chạy thủ công: python refresh_token.py")
            sys.exit(1)
        log("Token đã được làm mới.")
    if not verify_token():
        log("LỖI: Facebook token không hợp lệ. Dừng lại.")
        sys.exit(1)

    # 2. Scrape bài mới từ thebump.com
    log("Scraping thebump.com...")
    articles = get_new_articles(max_articles=3)

    if not articles:
        log("Không tìm thấy bài mới. Kết thúc.")
        return

    log(f"Tìm thấy {len(articles)} bài mới. Xử lý bài đầu tiên...")

    # 3. Chỉ đăng 1 bài/ngày (bài đầu tiên)
    article = articles[0]
    log(f"Bài được chọn: {article['title']}")

    # 4. AI xử lý: tạo caption + ảnh
    log("AI đang tạo caption và ảnh...")
    processed = process_article(article)
    log(f"Caption:\n{processed['caption'][:200]}...")

    # 5. Lưu ảnh xuống disk
    if processed.get("image_bytes"):
        img_path = save_image(processed["image_bytes"], article["title"])
        log(f"Ảnh đã lưu: {img_path}")

    # 6. Đăng lên Facebook
    log("Đăng lên Facebook Page...")
    result = post_article(processed)

    # 7. Lưu URL đã đăng
    save_posted_url(article["url"])
    log(f"Hoàn thành! Facebook post ID: {result.get('post_id') or result.get('id')}")
    log("=" * 50)


def main():
    try:
        asyncio.run(run())
    except Exception as e:
        log(f"LỖI NGHIÊM TRỌNG: {e}")
        log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

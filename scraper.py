"""
scraper.py - Lấy bài viết từ thebump.com qua Google News RSS feed
"""
import json
import xml.etree.ElementTree as ET
import re
import requests
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=site:thebump.com+pregnancy+tips&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:thebump.com+baby+care&hl=en-US&gl=US&ceid=US:en",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def load_posted_urls() -> set:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("posted_urls", []))
    return set()


def save_posted_url(url: str):
    posted = load_posted_urls()
    posted.add(url)
    STATE_FILE.write_text(
        json.dumps({"posted_urls": list(posted)}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _guess_category(title: str) -> str:
    text = title.lower()
    if any(w in text for w in ["baby", "infant", "newborn", "toddler", "postpartum"]):
        return "baby"
    return "pregnancy"


def get_new_articles(max_articles: int = 3) -> list[dict]:
    """Lấy các bài mới chưa đăng từ Google News RSS của thebump.com."""
    posted_urls = load_posted_urls()
    seen_titles = set()
    results = []

    for feed_url in GOOGLE_NEWS_FEEDS:
        if len(results) >= max_articles:
            break
        try:
            resp = requests.get(feed_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.findall(".//item"):
                if len(results) >= max_articles:
                    break

                title_el = item.find("title")
                link_el  = item.find("link")
                desc_el  = item.find("description")

                title = _clean_html(title_el.text or "") if title_el is not None else ""
                link  = (link_el.text or "").strip() if link_el is not None else ""
                desc  = _clean_html(desc_el.text or "") if desc_el is not None else ""

                # Bỏ suffix "- The Bump"
                title = re.sub(r"\s*[-|]\s*The Bump\s*$", "", title).strip()

                # Dùng title làm key dedup (URL là Google redirect, không dùng được)
                title_key = title.lower()
                if not title or title_key in seen_titles or link in posted_urls:
                    continue

                seen_titles.add(title_key)
                results.append({
                    "url": link,           # Google News link, dùng để track đã đăng
                    "title": title,
                    "excerpt": desc[:400],
                    "thumbnail": "",
                    "category": _guess_category(title),
                    "content": desc,
                })

        except Exception as e:
            print(f"  Loi RSS: {e}")

    print(f"  Tim thay {len(results)} bai moi.")
    return results


if __name__ == "__main__":
    articles = get_new_articles(max_articles=3)
    for a in articles:
        print(f"\n--- {a['title']} ---")
        print(f"Category: {a['category']}")
        print(f"Excerpt: {a['excerpt'][:150]}")

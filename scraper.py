"""
scraper.py - Lấy bài viết từ thebump.com qua Google News RSS feed
"""
import json
import xml.etree.ElementTree as ET
import re
import requests
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

BASE_EN = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="
BASE_VN = "https://news.google.com/rss/search?hl=vi&gl=VN&ceid=VN:vi&q="

SOURCES_EN = "site:thebump.com+OR+site:babycenter.com+OR+site:whattoexpect.com+OR+site:parents.com+OR+site:healthychildren.org"
SOURCES_VN = "site:marrybaby.vn+OR+site:eva.vn/lam-me"

GOOGLE_NEWS_FEEDS = [
    # --- Nguồn EN (nội dung gốc chất lượng cao) ---
    # Pregnancy
    BASE_EN + f"({SOURCES_EN})+pregnancy+tips",
    # 6-12 tháng
    BASE_EN + f"({SOURCES_EN})+baby+crawling+sitting+teething",
    BASE_EN + f"({SOURCES_EN})+baby+solid+foods+6+months",
    # 12-24 tháng
    BASE_EN + f"({SOURCES_EN})+toddler+walking+talking+12+months",
    BASE_EN + f"({SOURCES_EN})+baby+home+safety+toddler",
    # 2-3 tuổi
    BASE_EN + f"({SOURCES_EN})+toddler+preschool+discipline",
    BASE_EN + f"({SOURCES_EN})+toddler+behavior+temperament+2+years",

    # --- Nguồn VN (insight chủ đề trending mẹ bỉm VN) ---
    BASE_VN + f"({SOURCES_VN})+mang+thai",
    BASE_VN + f"({SOURCES_VN})+ăn+dặm+cho+bé",
    BASE_VN + f"({SOURCES_VN})+nuôi+con+nhỏ",
    BASE_VN + f"({SOURCES_VN})+trẻ+sơ+sinh",
    BASE_VN + f"({SOURCES_VN})+bé+tập+đi",
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
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return text.strip()


HOMEPAGE_PATTERNS = [
    r"^Parents: Trusted Parenting",
    r"^HealthyChildren\.org - From",
    r"^BabyCenter\s*[-|]",
    r"^What to Expect\s*[-|]",
    r"^MarryBaby\s*[-|]",
    r"^Eva\.vn\s*[-|]",
]

def _is_homepage(title: str, excerpt: str) -> bool:
    """Lọc bỏ kết quả là trang chủ, không phải bài viết."""
    for pat in HOMEPAGE_PATTERNS:
        if re.search(pat, title):
            return True
    # Excerpt quá ngắn = không phải bài viết thực
    if len(excerpt.strip()) < 50:
        return True
    return False


def _guess_category(title: str) -> str:
    text = title.lower()
    if any(w in text for w in ["pregnant", "pregnancy", "trimester", "prenatal", "due date", "morning sickness", "labor", "birth", "maternity", "bump",
                                "mang thai", "bầu", "thai kỳ", "sinh con", "sau sinh", "hậu sản"]):
        return "pregnancy"
    if any(w in text for w in ["preschool", "discipline", "tantrum", "2-year", "3-year", "two year", "three year",
                                "2 tuổi", "3 tuổi", "mầm non", "kỷ luật", "ăn vạ", "giận dỗi"]):
        return "toddler_2_3"
    if any(w in text for w in ["walking", "first steps", "talking", "first words", "12 month", "18 month", "home safety", "childproof",
                                "tập đi", "tập nói", "12 tháng", "18 tháng", "an toàn"]):
        return "toddler_12_24"
    if any(w in text for w in ["crawl", "sitting", "teething", "solid food", "weaning", "6 month", "9 month",
                                "ăn dặm", "mọc răng", "lật", "bò", "6 tháng", "9 tháng"]):
        return "baby_6_12"
    return "baby"


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

                # Bỏ suffix nguồn EN và VN
                title = re.sub(r"\s*[-|]\s*The Bump\s*$", "", title).strip()
                title = re.sub(r"\s*[-|]\s*(MarryBaby|Eva\.vn|Marry Baby)\s*$", "", title).strip()

                # Dùng title làm key dedup (URL là Google redirect, không dùng được)
                title_key = title.lower()
                if not title or title_key in seen_titles or link in posted_urls:
                    continue
                if _is_homepage(title, desc):
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

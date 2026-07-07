"""
scraper.py - Lấy bài về AI / công nghệ từ nhiều nguồn RSS/Atom uy tín quốc tế
cho page "Nguyên Học AI".

Hỗ trợ cả RSS 2.0 (<item>, <link>text</link>) lẫn Atom (<entry>, <link href=...>).
Nguồn nào không có RSS chính chủ (Anthropic, Meta AI, Microsoft) thì phủ qua
Google News RSS bằng truy vấn site:.
"""
import json
import random
import xml.etree.ElementTree as ET
import re
import requests
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

# --- Google News RSS (fallback cho nguồn không có RSS chính chủ) ---
GNEWS = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="

# Category: ai_news | ai_howto | ai_tools | tech
# ai_feed=True  -> nguồn chuyên AI, lấy hết bài (không cần lọc chủ đề)
# ai_feed vắng  -> nguồn tổng hợp, bài phải trúng keyword AI/công nghệ mới lấy
FEEDS = [
    # === 📰 Tin AI / công nghệ ===
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/", "cat": "tech"},
    {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml", "cat": "tech"},
    {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/index", "cat": "tech"},
    {"name": "TechCrunch AI",   "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "cat": "ai_news", "ai_feed": True},
    {"name": "VentureBeat AI",  "url": "https://venturebeat.com/category/ai/feed/", "cat": "ai_news", "ai_feed": True},
    {"name": "Wired AI",        "url": "https://www.wired.com/feed/tag/ai/latest/rss", "cat": "ai_news", "ai_feed": True},
    {"name": "The Register",    "url": "https://www.theregister.com/headlines.atom", "cat": "tech"},
    {"name": "AI News",         "url": "https://www.artificialintelligence-news.com/feed/", "cat": "ai_news", "ai_feed": True},
    {"name": "MarkTechPost",    "url": "https://www.marktechpost.com/feed/", "cat": "ai_news", "ai_feed": True},

    # === 🏢 Blog chính chủ lab AI (nguồn gốc) ===
    {"name": "OpenAI",          "url": "https://openai.com/news/rss.xml", "cat": "ai_news", "ai_feed": True},
    {"name": "Google AI",       "url": "https://blog.google/technology/ai/rss/", "cat": "ai_news", "ai_feed": True},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "cat": "ai_news", "ai_feed": True},
    {"name": "Hugging Face",    "url": "https://huggingface.co/blog/feed.xml", "cat": "ai_howto", "ai_feed": True},
    {"name": "Mistral AI",      "url": "https://mistral.ai/rss.xml", "cat": "ai_news", "ai_feed": True},

    # === 🛠️ Thực hành / cách dùng AI (feed tổng hợp -> lọc theo keyword) ===
    {"name": "Zapier",          "url": "https://zapier.com/blog/feeds/latest/", "cat": "ai_howto"},
    {"name": "Simon Willison",  "url": "https://simonwillison.net/atom/everything/", "cat": "ai_howto"},
    {"name": "Tom's Guide",     "url": "https://www.tomsguide.com/feeds/all", "cat": "ai_tools"},

    # === 🔁 Google News fallback (lab không có RSS) ===
    {"name": "Anthropic",       "url": GNEWS + "site:anthropic.com", "cat": "ai_news", "gnews": True, "ai_feed": True},
    {"name": "Meta AI",         "url": GNEWS + "site:ai.meta.com",   "cat": "ai_news", "gnews": True, "ai_feed": True},
    {"name": "Microsoft AI",    "url": GNEWS + '"Microsoft"+Copilot+AI', "cat": "ai_tools", "gnews": True, "ai_feed": True},
]

# Chỉ áp cho nguồn tổng hợp: bài phải nhắc tới AI/công nghệ số mới giữ
_RELEVANT = re.compile(
    r"\b(?:artificial intelligence|machine learning|deep learning|neural|"
    r"ai|ml|llm|llms|chatbot|generative|genai|agentic|agent|prompt|"
    r"chatgpt|gpt|openai|anthropic|claude|gemini|deepmind|llama|mistral|"
    r"copilot|midjourney|grok|perplexity|hugging ?face|nvidia|gpu|chip|"
    r"semiconductor|data ?cent(?:er|re)|cloud|software|app|application|saas|"
    r"coding|code|developer|programming|api|algorithm|automation|robot|"
    r"cyber|malware|smartphone|gadget|quantum|startup)\b",
    re.I,
)


def _is_relevant(feed: dict, title: str, excerpt: str) -> bool:
    """Feed chuyên AI -> luôn hợp lệ. Feed tổng hợp -> phải trúng keyword."""
    if feed.get("ai_feed"):
        return True
    return bool(_RELEVANT.search(f"{title} {excerpt}"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def load_posted_urls() -> set:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("posted_urls", []))
    return set()


def save_posted_url(url: str):
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    else:
        data = {}
    posted = set(data.get("posted_urls", []))
    posted.add(url)
    data["posted_urls"] = list(posted)
    STATE_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
                .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
                .replace("&hellip;", "..."))
    return re.sub(r"\s+", " ", text).strip()


# ---------- Parse helper: hỗ trợ cả RSS lẫn Atom, bỏ qua namespace ----------

def _local(tag: str) -> str:
    """Trả về local-name, bỏ phần {namespace}."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _iter_items(root):
    for el in root.iter():
        if _local(el.tag) in ("item", "entry"):
            yield el


def _child_text(item, names: tuple) -> str:
    for ch in item:
        if _local(ch.tag) in names:
            return (ch.text or "").strip()
    return ""


def _get_link(item) -> str:
    """RSS: <link>url</link> | Atom: <link href=... rel=alternate/>."""
    fallback = ""
    for ch in item:
        if _local(ch.tag) != "link":
            continue
        href = ch.get("href")
        if href:
            if ch.get("rel", "alternate") == "alternate":
                return href.strip()
            fallback = fallback or href.strip()
        elif ch.text and ch.text.strip():
            return ch.text.strip()
    if fallback:
        return fallback
    for names in (("guid",), ("id",)):
        val = _child_text(item, names)
        if val.startswith("http"):
            return val
    return ""


# ---------- Phân loại category ----------

_HOWTO_KW = ["how to", "how-to", "guide", "tutorial", "tips", "step-by-step",
             "step by step", "ways to", "prompt", "beginner", "getting started",
             "productivity", "workflow", "cheat sheet", "explained", "what is"]
_TOOLS_KW = [" vs ", " vs. ", "best ", "top ", "review", "alternative",
             "comparison", "compared", "which ai", "roundup"]
_NEWS_KW = ["launch", "release", "announce", "unveil", "introduc", "raises",
            "funding", "acquire", "rolls out", "new model", "update", "debut",
            "gpt-", "gemini", "claude", "llama", "open-source", "open source"]


def _guess_category(title: str, default_cat: str) -> str:
    """Tinh chỉnh category theo keyword, nếu không khớp thì giữ default của nguồn."""
    t = title.lower()
    if any(k in t for k in _HOWTO_KW):
        return "ai_howto"
    if any(k in t for k in _TOOLS_KW):
        return "ai_tools"
    if any(k in t for k in _NEWS_KW):
        return "ai_news"
    return default_cat


# ---------- Lọc rác ----------

def _is_junk(title: str, excerpt: str, content: str) -> bool:
    if not title or len(title) < 8:
        return True
    # Không có mô tả lẫn nội dung -> khả năng cao là trang mục lục / rác
    if len((excerpt or content).strip()) < 40:
        return True
    return False


def get_new_articles(max_articles: int = 3) -> list[dict]:
    """Lấy các bài AI/công nghệ mới chưa đăng từ các nguồn RSS/Atom uy tín."""
    posted_urls = load_posted_urls()
    seen_titles = set()
    seen_links = set()
    results = []
    MAX_PER_FEED = 2  # tránh 1 nguồn chiếm hết -> nội dung đa dạng

    feeds = FEEDS[:]
    random.shuffle(feeds)  # đổi thứ tự mỗi lần chạy -> nội dung đa dạng theo nguồn

    for feed in feeds:
        if len(results) >= max_articles:
            break
        from_this_feed = 0
        try:
            resp = requests.get(feed["url"], headers=HEADERS, timeout=20)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in _iter_items(root):
                if len(results) >= max_articles or from_this_feed >= MAX_PER_FEED:
                    break

                title = _clean_html(_child_text(item, ("title",)))
                link = _get_link(item)
                # Nội dung: ưu tiên content:encoded / content, fallback description/summary
                raw_content = _child_text(item, ("encoded", "content"))
                raw_desc = _child_text(item, ("description", "summary"))
                excerpt = _clean_html(raw_desc or raw_content)
                content = _clean_html(raw_content or raw_desc)

                # Google News: bỏ đuôi " - Publisher" trong title
                if feed.get("gnews"):
                    title = re.sub(r"\s+-\s+[^-]+$", "", title).strip()

                title_key = title.lower()
                if not title or title_key in seen_titles:
                    continue
                if link in posted_urls or link in seen_links:
                    continue
                if _is_junk(title, excerpt, content):
                    continue
                if not _is_relevant(feed, title, excerpt):
                    continue

                seen_titles.add(title_key)
                seen_links.add(link)
                from_this_feed += 1
                results.append({
                    "url": link,
                    "title": title,
                    "excerpt": excerpt[:400],
                    "thumbnail": "",
                    "category": _guess_category(title, feed["cat"]),
                    "content": content[:2000],
                    "source": feed["name"],
                })

        except Exception as e:
            print(f"  Loi RSS [{feed['name']}]: {e}")

    print(f"  Tim thay {len(results)} bai moi.")
    return results


if __name__ == "__main__":
    articles = get_new_articles(max_articles=5)
    for a in articles:
        print(f"\n--- {a['title']} ---")
        print(f"Nguồn: {a['source']}  |  Category: {a['category']}")
        print(f"Link: {a['url']}")
        print(f"Excerpt: {a['excerpt'][:150]}")

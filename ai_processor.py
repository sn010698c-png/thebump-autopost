"""
ai_processor.py - Dùng OpenAI để:
1. Dịch + viết caption Facebook tiếng Việt (gpt-5.4-mini)
2. Tạo ảnh minh hoạ (gpt-image-2)
"""
import os
import io
import base64
from pathlib import Path
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

_SKILL_PATH = Path(__file__).parent / "skill_content.md"
CONTENT_SKILL = _SKILL_PATH.read_text(encoding="utf-8") if _SKILL_PATH.exists() else ""

TEXT_MODEL = "gpt-5.4-mini"
IMAGE_MODEL = "gpt-image-2"


_LOAI_BAI_CYCLE = ["A", "B", "C", "D", "E"]
_LOAI_BAI_DESC = {
    "A": "Trải nghiệm cá nhân — kể 1 lần mình dùng AI làm việc gì đó, kết quả ra sao, học được gì.",
    "B": "Mẹo / hướng dẫn — chỉ cách dùng AI cho 1 việc cụ thể, có ví dụ prompt / thao tác làm theo được ngay.",
    "C": "Tương tác / câu hỏi — hỏi mọi người đang dùng AI thế nào, tool gì, gặp khó gì; khơi comment.",
    "D": "Góc nhìn / cảnh báo — rủi ro, sai lầm hay gặp khi dùng AI (bị AI bịa thông tin, lộ dữ liệu...), nhắc mọi người tỉnh táo, không hù doạ.",
    "E": "Tin nóng + bình luận — đưa 1 tin AI/công nghệ mới kèm góc nhìn cá nhân: nó có ý nghĩa gì với người thường.",
}


def _pick_loai_bai() -> str:
    """Luân phiên loại bài A→B→C→D→E→A dựa trên state.json."""
    import json
    from pathlib import Path as P
    state_file = P(__file__).parent / "state.json"
    data = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    last_idx = data.get("last_loai_bai_idx", -1)
    next_idx = (last_idx + 1) % len(_LOAI_BAI_CYCLE)
    data["last_loai_bai_idx"] = next_idx
    state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return _LOAI_BAI_CYCLE[next_idx]


def generate_caption(article: dict) -> str:
    """Tạo caption Facebook tiếng Việt từ bài viết."""
    title    = article.get("title", "")
    excerpt  = article.get("excerpt", "")
    content  = article.get("content", "")[:1500]
    category = article.get("category", "ai_news")

    loai_bai = _pick_loai_bai()

    category_context = {
        "ai_news":  "tin AI mới (model, tính năng, thương vụ, chính sách) — giải thích dễ hiểu, nói rõ ảnh hưởng gì tới người dùng bình thường",
        "ai_howto": "hướng dẫn / mẹo dùng AI — từng bước dễ làm, có ví dụ prompt copy làm theo được ngay",
        "ai_tools": "công cụ AI (review, so sánh) — nói thẳng cái nào hợp việc gì, ai nên dùng, trung thực có hay có dở",
        "tech":     "công nghệ chung — liên hệ đời sống người Việt, gần gũi dễ hiểu",
    }.get(category, "AI và công nghệ cho người Việt")

    if category == "ai_howto":
        persona_note = """Đây là bài HƯỚNG DẪN → cho ít nhất 1 ví dụ prompt hoặc thao tác cụ thể mà người đọc copy làm theo được ngay.
Ưu tiên 'đọc xong làm được liền'. Có thể dùng tối đa 3 bullet nếu là các bước."""
    elif category == "ai_tools":
        persona_note = """Đây là bài về CÔNG CỤ → nói rõ tool này hợp việc gì, ai nên dùng. Trung thực: có điểm hay, có điểm dở. Không quảng cáo lố."""
    elif category == "tech":
        persona_note = """Đây là tin CÔNG NGHỆ → kể góc 'tin này hay nè cả nhà', liên hệ đời sống người Việt bình thường."""
    else:  # ai_news
        persona_note = """Đây là TIN AI → giải thích tin thật dễ hiểu, luôn trả lời: tin này ảnh hưởng gì tới người dùng bình thường? Đừng đưa tin khan."""

    prompt = f"""Mày là NGUYÊN — người Việt mê công nghệ, tự học và dùng AI mỗi ngày, admin page "Nguyên Học AI".
Mày chia sẻ về {category_context}.
Xưng "mình", gọi người đọc là "cả nhà" / "mọi người". KHÔNG bán hàng, KHÔNG chèn sản phẩm — mục tiêu là cho giá trị + kéo tương tác.

{persona_note}

Loại bài hôm nay: **{loai_bai}** — {_LOAI_BAI_DESC[loai_bai]}

Dựa trên bài sau, viết 1 bài Facebook tiếng Việt tuân thủ TOÀN BỘ skill đã được nạp:

Tiêu đề gốc: {title}
Tóm tắt: {excerpt}
Nội dung: {content}

=== BÀI MẪU ĐÚNG GIỌNG ===
🤯 Mình nhờ ChatGPT viết email từ chối khách, xong mà nhẹ cả người

Hôm qua mình phải trả lời một khách khó tính, kiểu từ chối mà vẫn phải giữ lịch sự. Ngồi gõ xoá mấy lần vẫn thấy gượng.

Cuối cùng mình mở ChatGPT lên, gõ đúng một câu lệnh (prompt): "Viết giúp mình email từ chối yêu cầu giảm giá, giọng lịch sự, cảm ơn khách, giữ mối quan hệ."

15 giây sau nó trả về một bản mình chỉnh 2 chữ là gửi được luôn 😅

Cái mình nhận ra: AI không quyết thay mình, nó chỉ gỡ giúp cái đoạn "bí không biết mở lời sao". Càng nói rõ mình muốn gì (giọng gì, cho ai, dài ngắn ra sao) thì nó viết càng trúng.

Mẹo nhỏ nè cả nhà: đừng gõ cụt lủn "viết email từ chối". Hãy thêm bối cảnh + giọng điệu + người nhận. Khác một trời một vực đó.

Còn mọi người, đã ai thử nhờ AI viết tin nhắn khó nói chưa? Mình tò mò cả nhà hay dùng AI vào việc gì nhất, comment cho mình biết với nha 👇

#NguyenHocAI #ChatGPT #MeoAI #AI #CongNghe
=== KẾT THÚC MẪU ===

Chỉ trả về nội dung bài đăng, không giải thích thêm. KHÔNG đề cập nguồn bài gốc."""

    messages = []
    if CONTENT_SKILL:
        messages.append({"role": "system", "content": CONTENT_SKILL})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content.strip()


def generate_image(article: dict) -> bytes | None:
    """Tạo ảnh minh hoạ bằng OpenAI gpt-image-2."""
    title = article.get("title", "")
    category = article.get("category", "ai_news")

    style_map = {
        "ai_news":  "a clean modern illustration about artificial intelligence news, a person reading on a laptop or phone with subtle AI/neural network motifs, friendly tech vibe",
        "ai_howto": "a clean modern illustration of a person using an AI assistant on a laptop or smartphone to get work done, step-by-step helpful feeling, friendly and approachable",
        "ai_tools": "a clean modern illustration showing AI apps and tools on a screen, comparing options, sleek user-interface vibe, organized and clear",
        "tech":     "a clean modern illustration about technology and gadgets in everyday life, minimal and bright, friendly tech vibe",
    }
    style = style_map.get(category, style_map["ai_news"])

    prompt = f"""Create {style}.
The image should relate to the topic: {title[:100]}
Style: modern flat vector illustration, clean and minimal, blue and purple tech color palette with soft gradients, friendly and approachable (not cold or dystopian), no text, no scary robots, social media ready, 1:1 square format"""

    try:
        response = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            n=1,
            size="1024x1024",
            output_format="png",
        )
        img_b64 = response.data[0].b64_json
        return base64.b64decode(img_b64)

    except Exception as e:
        print(f"  Lỗi generate ảnh: {e}")
        return None


def add_watermark(image_bytes: bytes) -> bytes:
    """Chèn logo vào góc dưới phải của ảnh."""
    logo_path = Path(__file__).parent / "logo.png"
    if not logo_path.exists():
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo = 20% chiều rộng ảnh
    logo_w = int(img.width * 0.20)
    ratio = logo_w / logo.width
    logo_h = int(logo.height * ratio)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Đặt vào góc dưới phải, cách mép 16px
    padding = 16
    x = img.width - logo_w - padding
    y = img.height - logo_h - padding

    # Dùng alpha channel của logo làm mask
    img.paste(logo, (x, y), logo)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def process_article(article: dict) -> dict:
    """Xử lý 1 bài: tạo caption + ảnh."""
    print(f"  AI đang xử lý: {article['title'][:60]}...")

    caption = generate_caption(article)
    print(f"  Caption tạo xong ({len(caption)} ký tự)")

    image_bytes = generate_image(article)
    if image_bytes:
        image_bytes = add_watermark(image_bytes)
        print(f"  Ảnh tạo xong ({len(image_bytes)} bytes)")
    else:
        print("  Không tạo được ảnh, sẽ đăng text-only")

    return {
        **article,
        "caption": caption,
        "image_bytes": image_bytes,
    }


if __name__ == "__main__":
    test_article = {
        "title": "How to use ChatGPT to write better emails in seconds",
        "excerpt": "A simple prompting technique that turns a one-line request into a polished, professional email.",
        "content": "Instead of typing a vague request, give ChatGPT context, tone, and audience. For example: 'Write a polite email declining a discount request while keeping the relationship warm.' The more specific your prompt, the better the result...",
        "category": "ai_howto",
        "url": "https://example.com/chatgpt-emails",
    }

    result = process_article(test_article)
    print("\n=== CAPTION ===")
    print(result["caption"])
    if result["image_bytes"]:
        Path("test_image.png").write_bytes(result["image_bytes"])
        print("\nĐã lưu test_image.png")
    else:
        print("\nKhông có ảnh")

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
    "A": "Câu chuyện cá nhân — kể 1 tình huống thật với bé Bơ / anh Tú / bà nội, có cảm xúc, có bài học ngầm, dẫn về sản phẩm.",
    "B": "Mẹo hay / kiến thức — chia sẻ mẹo chăm con dưới dạng 'mình tìm hiểu được', không liệt kê khô cứng.",
    "C": "Tương tác / câu hỏi — hỏi mẹ bỉm về kinh nghiệm, tình huống cụ thể, khiến họ muốn comment.",
    "D": "Cảnh báo / pain point — kể sự cố tai nạn vặt đã xảy ra với Bơ hoặc nghe kể, cảnh tỉnh mẹ khác + gợi nhu cầu đồ an toàn.",
    "E": "Behind the scenes / đời thường — khoảnh khắc nhỏ đáng yêu, tạo cảm giác mẹ Mai là người thật.",
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
    category = article.get("category", "baby")

    bo_age = os.environ.get("BO_AGE", "18 tháng tuổi")
    loai_bai = _pick_loai_bai()

    category_context = {
        "pregnancy":      "mang thai, thai kỳ, sức khoẻ bà bầu",
        "baby":           "chăm sóc bé sơ sinh, nuôi con nhỏ",
        "baby_6_12":      "bé 6–12 tháng: tập bò, tập ngồi, mọc răng, ăn dặm",
        "toddler_12_24":  "bé 12–24 tháng: tập đi, tập nói, an toàn trong nhà",
        "toddler_2_3":    "bé 2–3 tuổi: mẫu giáo, tính cách, kỷ luật tích cực",
        "news":           "nuôi dạy con nhỏ",
    }.get(category, "nuôi dạy con nhỏ")

    is_pregnancy = category in ("pregnancy", "news")
    if is_pregnancy:
        persona_note = f"""Chủ đề mang thai → viết theo góc HỒI TƯỞNG: "hồi mang bầu Bơ...", "hồi mình còn bầu...".
KHÔNG kể đang mang thai hiện tại. KHÔNG đề cập tuổi Bơ trong phần hồi tưởng."""
    else:
        persona_note = f"""Chủ đề bé/toddler → Bơ đang {bo_age} hiện tại.
Tra bảng mốc phát triển trong skill để chọn đúng hành động phù hợp tuổi {bo_age}.
KHÔNG để Bơ ở tuổi khác, KHÔNG kể chuyện đang mang thai."""

    prompt = f"""Mày là MAI — mẹ bỉm 30 tuổi, admin page "Mẹ Khéo Con Khoẻ", chuyên về {category_context}.
Nhân vật: con gái Bơ ({bo_age}), chồng anh Tú, bà nội hay sang phụ chăm, bà ngoại ở quê.

{persona_note}

Loại bài hôm nay: **{loai_bai}** — {_LOAI_BAI_DESC[loai_bai]}

Dựa trên bài sau, viết 1 bài Facebook tiếng Việt tuân thủ TOÀN BỘ skill đã được nạp:

Tiêu đề gốc: {title}
Tóm tắt: {excerpt}
Nội dung: {content}

=== BÀI MẪU ĐÚNG GIỌNG ===
😭 KHÓC CẠN NƯỚC MẮT KHI BƠ NGÃ LẦN ĐẦU

Bơ nhà mình vừa biết vịn tay tập đi được 1 tuần. Hôm kia con đi 3 bước liền, cả nhà vỗ tay ầm ầm.

Hôm qua... con té ngửa ra sau đập đầu xuống sàn gạch. Tiếng "cộp" đó đến giờ mình vẫn nghe vang trong đầu 💔

Bơ khóc 10 phút không nín. Mình ôm con mà tay run lẩy bẩy, vội gọi anh Tú về chở 2 mẹ con lên viện. Bác sĩ bảo may không sao, nhưng mình sợ đến mức đêm đó thức trắng canh con.

Mẹ nào có con đang tập đi đọc đến đây chắc hiểu cảm giác này...

Mấy hôm nay mình tìm hiểu mới biết: lúc 12–18 tháng bé ngã trung bình 5–7 lần/ngày. Sàn gạch, góc bàn, cạnh tủ — toàn "hung thần" với Bơ. Từ hôm đó mình đầu tư hẳn đồ an toàn cho con, yên tâm hơn hẳn. Mẹ nào cần tham khảo thì inbox mình nha 💕

Các mẹ ơi, con mẹ tập đi lúc mấy tháng? Ngã nhiều nhất ở chỗ nào trong nhà? Comment kể mình nghe nhé 😭

#BeTapDi #MeBimSua #AnToanChoBe #MeKheoConKhoe
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
    category = article.get("category", "pregnancy")

    style_map = {
        "pregnancy":     "a warm, soft illustration of a happy pregnant Vietnamese woman, pastel colors, gentle lighting, cozy home setting",
        "baby":          "a cute illustration of a happy newborn baby girl, soft pastel colors, warm and cheerful, cartoon style",
        "baby_6_12":     "a cute illustration of a chubby baby girl crawling or eating solid foods, soft pastel colors, cheerful cartoon style",
        "toddler_12_24": "a cute illustration of a happy toddler girl taking first steps or playing safely at home, pastel colors, warm cartoon style",
        "toddler_2_3":   "a cute illustration of a playful toddler girl at preschool or playing with building blocks, soft pastel colors, cheerful cartoon style",
        "news":          "a gentle illustration of a Vietnamese mother and baby girl, soft colors, modern flat design",
    }
    style = style_map.get(category, style_map["pregnancy"])

    prompt = f"""Create {style}.
The image should relate to the topic: {title[:100]}
Style: warm, soft watercolor illustration, pastel pink and blue tones, no text, family-friendly, social media ready, 1:1 square format"""

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
        "title": "10 Best Pregnancy Foods for the First Trimester",
        "excerpt": "Eating right in the first trimester is crucial for your baby's development.",
        "content": "The first trimester is a critical time for fetal development. Foods rich in folate, iron, and calcium are essential...",
        "category": "pregnancy",
        "url": "https://www.thebump.com/a/test",
    }

    result = process_article(test_article)
    print("\n=== CAPTION ===")
    print(result["caption"])
    if result["image_bytes"]:
        Path("test_image.png").write_bytes(result["image_bytes"])
        print("\nĐã lưu test_image.png")
    else:
        print("\nKhông có ảnh")

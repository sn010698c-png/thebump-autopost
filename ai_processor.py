"""
ai_processor.py - Dùng Google AI Studio (Gemini) để:
1. Dịch + viết caption Facebook tiếng Việt
2. Tạo ảnh minh hoạ bằng Gemini 2.0 Flash (image generation)
"""
import os
import io
import base64
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"


def generate_caption(article: dict) -> str:
    """Tạo caption Facebook tiếng Việt từ bài viết thebump.com."""
    title = article.get("title", "")
    excerpt = article.get("excerpt", "")
    content = article.get("content", "")[:1500]
    category = article.get("category", "pregnancy")

    category_context = {
        "pregnancy":      "mang thai, thai kỳ, sức khoẻ bà bầu",
        "baby":           "chăm sóc bé sơ sinh, nuôi con nhỏ",
        "baby_6_12":      "bé 6-12 tháng: tập bò, tập ngồi, mọc răng, ăn dặm",
        "toddler_12_24":  "bé 12-24 tháng: tập đi, tập nói, an toàn trong nhà",
        "toddler_2_3":    "bé 2-3 tuổi: mẫu giáo, tính cách, kỷ luật tích cực",
        "news":           "tin tức mới nhất về thai kỳ và em bé",
    }.get(category, "mang thai và chăm sóc bé")

    baby_name = "Bơ"
    bo_age = os.environ.get("BO_AGE", "8 tháng tuổi")

    # Xác định bài là về mang thai hay về bé đã sinh
    is_pregnancy = category in ("pregnancy", "news")

    if is_pregnancy:
        persona = f"""Mày là admin page, có con {baby_name} hiện {bo_age}.
Bài này về chủ đề mang thai → viết theo góc nhìn HỒI TƯỞNG: "hồi mang bầu {baby_name}..." hoặc "hồi mình mang thai...".
KHÔNG kể Bơ đang trong bụng hay đang mang thai hiện tại."""
    else:
        persona = f"""Mày là admin page, có con {baby_name} hiện {bo_age}.
Bài này về chủ đề bé/toddler → viết nhất quán: {baby_name} đang ở độ tuổi {bo_age}.
KHÔNG để Bơ ở độ tuổi khác, KHÔNG kể chuyện đang mang thai."""

    prompt = f"""Mày là admin Facebook Page "Mẹ Khéo Con Khoẻ" - trang chuyên về {category_context}.
Page bán đồ an toàn cho bé, đồ ngủ và đồ tiện ích cho bé 6-36 tháng.

{persona}

Dựa trên bài viết tiếng Anh sau, viết 1 bài Facebook tiếng Việt theo đúng PHONG CÁCH bên dưới:

Tiêu đề gốc: {title}
Tóm tắt: {excerpt}
Nội dung: {content}

=== PHONG CÁCH BẮT BUỘC ===

1. Ngôi thứ nhất: dùng "mình", KHÔNG dùng "tôi" hay "chúng ta"
2. Mở bài bằng CÂU CHUYỆN CÁ NHÂN (3-4 câu): kể về em bé tên "{baby_name}" nhà mình - một tình huống cụ thể, cảm xúc thật, liên quan đến chủ đề bài
3. Dùng "các mẹ", "mẹ ơi" - KHÔNG dùng "bạn"
4. CẤM các cụm từ sau: "giai đoạn này", "vượt bậc", "tuyệt vời", "khám phá", "hãy cùng", "đừng bỏ lỡ", "người bạn đồng hành", "lột xác", "chuyển mình lớn lao", "dung hòa cảm xúc", "cân bằng giữa"
5. Nhắc tên "{baby_name}" ít nhất 2 lần trong bài
6. Kết bài bằng 1 câu hỏi MỞ CỤ THỂ (không hỏi chung chung):
   - SAI: "Các mẹ có kinh nghiệm gì không?"
   - ĐÚNG: "Con mẹ nào bị [triệu chứng cụ thể] lúc mấy tuần? Comment cho mình biết với!"
7. Độ dài: 150-250 từ, KHÔNG quá 300 từ
8. Nếu dùng bullet point: tối đa 3 cái. Bài kể chuyện thì KHÔNG dùng bullet
9. Hashtag cuối bài: 4-5 hashtag KHÔNG DẤU tiếng Việt. Bắt buộc có #MeKheoConKhoe (đúng chính tả, KHÔNG phải #MeKhoeConKhoe)
10. Lồng ghép tự nhiên 1 câu liên quan đến sản phẩm an toàn/tiện ích cho bé (không quảng cáo lộ liễu)

=== GIỌNG VĂN: VĂN NÓI, KHÔNG PHẢI VĂN VIẾT ===
- Câu ngắn. Có chấm lửng khi cần... Có emoji cảm xúc phù hợp
- Chi tiết CỤ THỂ, thân xác: "bụng nhão", "rụng tóc từng mảng", "đau lưng không ngồi được", "ngực căng tức"
- Mẹ bỉm ở Kon Tum, Hà Giang, Cần Thơ phải hiểu và relate ngay
- TUYỆT ĐỐI KHÔNG dùng thuật ngữ phương Tây/học thuật chưa phổ biến ở VN
- Nếu bài gốc có khái niệm lạ (ví dụ "matrescence", "sleep regression", "wonder weeks"...) → PHẢI đổi thành cách diễn đạt Việt thông thường:
  ❌ "Matrescence - hành trình trở thành mẹ"
  ✅ "mình tìm hiểu mới biết, mẹ nào sinh xong cũng trải qua giai đoạn này hết các mẹ ạ"
  ❌ "sleep regression"
  ✅ "đột nhiên con không chịu ngủ, thức đến 2-3 giờ sáng"

=== BÀI MẪU ĐÚNG GIỌNG ===
😭 KHÓC CẠN NƯỚC MẮT KHI CON NGÃ LẦN ĐẦU

Con Nhím nhà mình vừa biết vịn tay tập đi được 1 tuần. Hôm kia nó đi 3 bước liền, cả nhà vỗ tay ầm ầm.

Hôm qua... nó té ngửa ra sau đập đầu xuống sàn gạch. Tiếng "cộp" đó đến giờ mình vẫn nghe vang trong đầu 💔

Nhím khóc 10 phút không nín. Mình ôm con mà tay run lẩy bẩy, vội gọi ông xã về chở 2 mẹ con lên viện. Bác sĩ bảo may không sao, nhưng mình sợ đến mức đêm đó thức trắng canh con.

Mẹ nào có con đang tập đi đọc đến đây chắc hiểu cảm giác này...

Mấy hôm nay mình tìm hiểu mới biết: giai đoạn 9-18 tháng là lúc bé ngã trung bình 5-7 lần/ngày. Sàn gạch, góc bàn, cạnh tủ - toàn "hung thần" với con mình. Miếng xốp lót sàn mình mới trải xong mà vẫn thấy chưa đủ yên tâm.

Các mẹ ơi, con mẹ ngã lần đầu lúc mấy tháng? Mẹ dùng cách gì để bảo vệ con? Comment chia sẻ cho mình với, mình đang gom kinh nghiệm 😭

#ContapDi #MeBimSua #AnToanChoBe #MeKheoConKhoe

=== KẾT THÚC MẪU ===

Chỉ trả về nội dung bài đăng, không giải thích thêm. KHÔNG đề cập thebump.com."""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
    )
    return response.text.strip()


def generate_image(article: dict) -> bytes | None:
    """Tạo ảnh minh hoạ bằng Gemini image generation."""
    title = article.get("title", "")
    category = article.get("category", "pregnancy")

    style_map = {
        "pregnancy":     "a warm, soft illustration of a happy pregnant woman, pastel colors, gentle lighting, cozy home setting",
        "baby":          "a cute illustration of a happy newborn baby, soft pastel colors, warm and cheerful, cartoon style",
        "baby_6_12":     "a cute illustration of a chubby baby crawling or eating solid foods, soft pastel colors, cheerful cartoon style",
        "toddler_12_24": "a cute illustration of a happy toddler taking first steps or playing safely at home, pastel colors, warm cartoon style",
        "toddler_2_3":   "a cute illustration of a playful toddler at preschool or playing with building blocks, soft pastel colors, cheerful cartoon style",
        "news":          "a gentle illustration related to pregnancy and baby care, soft colors, modern flat design",
    }
    style = style_map.get(category, style_map["pregnancy"])

    prompt = f"""Create {style}.
The image should relate to the topic: {title[:100]}
Style: warm, soft watercolor illustration, pastel pink and blue tones, no text, family-friendly, social media ready, 1:1 square format"""

    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                if isinstance(image_data, str):
                    image_data = base64.b64decode(image_data)
                return image_data

        print("  Gemini không trả về ảnh trong response.")
        return None

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

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
        "pregnancy": "mang thai, thai kỳ, sức khoẻ bà bầu",
        "baby": "chăm sóc bé, sơ sinh, nuôi con",
        "news": "tin tức mới nhất về thai kỳ và em bé",
    }.get(category, "mang thai và chăm sóc bé")

    prompt = f"""Bạn là content creator Facebook chuyên về chủ đề {category_context}.

Dựa trên bài viết tiếng Anh sau từ thebump.com, hãy viết 1 bài đăng Facebook tiếng Việt hấp dẫn:

Tiêu đề gốc: {title}
Tóm tắt: {excerpt}
Nội dung: {content}

YÊU CẦU:
- Viết hoàn toàn bằng tiếng Việt, tự nhiên, gần gũi
- Bắt đầu bằng 1-2 câu hook thu hút sự chú ý (câu hỏi hoặc sự thật thú vị)
- Nội dung chính: 3-5 điểm quan trọng, trình bày rõ ràng
- Kết thúc bằng 1 câu CTA nhẹ nhàng (mời like/share/bình luận)
- Thêm 4-6 hashtag tiếng Việt phù hợp (ví dụ: #MangThai #BàuBí #ChămsócBé #ThaiKỳ)
- Độ dài: 150-250 từ
- KHÔNG đề cập nguồn thebump.com

Chỉ trả về nội dung bài đăng, không giải thích thêm."""

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
        "pregnancy": "a warm, soft illustration of a happy pregnant woman, pastel colors, gentle lighting, cozy home setting",
        "baby": "a cute illustration of a happy baby or toddler, soft pastel colors, warm and cheerful, cartoon style",
        "news": "a gentle illustration related to pregnancy and baby care, soft colors, modern flat design",
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


def process_article(article: dict) -> dict:
    """Xử lý 1 bài: tạo caption + ảnh."""
    print(f"  AI đang xử lý: {article['title'][:60]}...")

    caption = generate_caption(article)
    print(f"  Caption tạo xong ({len(caption)} ký tự)")

    image_bytes = generate_image(article)
    if image_bytes:
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

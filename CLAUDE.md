# thebump-autopost

Script Python tự động scrape bài từ nhiều nguồn (thebump.com, babycenter.com, parents.com...), dùng Gemini AI tạo caption tiếng Việt + ảnh minh hoạ, rồi đăng lên Facebook Page **"Mẹ Khéo Con Khoẻ"** mỗi ngày 2 lần (8h sáng + 5h chiều).

## Flow

```
Google News RSS (multi-source) → Gemini AI → Facebook Graph API
```

1. `scraper.py` – Lấy bài từ 7 RSS feed theo chủ đề, từ nhiều nguồn
2. `ai_processor.py` – Gemini tạo caption tiếng Việt (đúng giọng mẹ bỉm) + ảnh minh hoạ
3. `facebook_poster.py` – Đăng ảnh + caption lên Facebook Page qua Graph API
4. `main.py` – Orchestrator: token check → scrape → AI → lưu ảnh → đăng FB → log
5. `refresh_token.py` – Tự động làm mới Facebook token

## Cấu trúc thư mục

```
thebump-autopost/
├── main.py               # Entry point
├── scraper.py            # Google News RSS multi-source scraper
├── ai_processor.py       # Gemini: caption TV + image gen
├── facebook_poster.py    # Facebook Graph API v19.0
├── refresh_token.py      # Tự động refresh Facebook token
├── .env                  # API keys + config (không commit)
├── state.json            # URL đã đăng (tránh trùng)
├── images/
│   └── YYYY-MM-DD/       # Ảnh AI tạo, lưu theo ngày
├── logs/
│   └── run.log           # Log mỗi lần chạy
├── .github/
│   └── workflows/
│       └── autopost.yml  # GitHub Actions workflow
├── requirements.txt
└── setup_scheduler.bat   # Đăng ký Windows Task Scheduler (backup)
```

## Cấu hình (.env)

```
GEMINI_API_KEY=     # aistudio.google.com/apikey
FB_PAGE_TOKEN=      # Page Access Token (KHÔNG phải User Token)
FB_PAGE_ID=         # ID của Facebook Page
FB_APP_ID=          # App ID từ Meta for Developers
FB_APP_SECRET=      # App Secret từ Meta for Developers
FB_USER_TOKEN=      # Long-lived User Token (60 ngày)
BO_AGE=8 tháng tuổi  # Tuổi bé Bơ hiện tại - cập nhật thủ công mỗi vài tháng
```

**Lưu ý quan trọng:**
- `FB_PAGE_TOKEN` phải là **Page Token**, lấy qua `GET /me/accounts` từ User Token
- `BO_AGE` dùng để giữ logic nội dung nhất quán (xem phần Content Logic)

## Facebook Page

- **Tên:** Mẹ Khéo Con Khoẻ
- **ID:** 166281259901889

## Models Gemini

- **Text:** `gemini-2.5-flash`
- **Image:** `gemini-2.5-flash-image`

## Nguồn crawl

7 RSS feed theo chủ đề, từ các nguồn: **thebump.com, babycenter.com, whattoexpect.com, parents.com, healthychildren.org**

| Feed | Chủ đề |
|---|---|
| pregnancy tips | Mang thai chung |
| crawling, sitting, teething | Bé 6-12 tháng |
| solid foods 6 months | Ăn dặm |
| walking, talking 12 months | Bé 12-24 tháng |
| home safety toddler | An toàn trong nhà |
| preschool discipline | Bé 2-3 tuổi |
| behavior temperament 2 years | Tính cách, kỷ luật |

Category tự động nhận diện từ title → dùng đúng persona + prompt ảnh cho từng nhóm tuổi.

## Content Logic (quan trọng)

**Nhân vật:** Bé **Bơ** nhà mình, hiện `BO_AGE` tuổi (lấy từ `.env`).

**Rule xử lý theo category:**
- Bài về **bé/toddler** → kể Bơ đang ở độ tuổi `BO_AGE` hiện tại
- Bài về **mang thai** → viết dạng **hồi tưởng** ("hồi mang bầu Bơ...", không kể đang mang thai)

→ Tránh tình trạng bài thì Bơ đang trong bụng, bài thì đã 8 tháng.

**Cập nhật tuổi Bơ:** Sửa `BO_AGE` trong `.env` + secret `BO_AGE` trên GitHub Actions.

## Rules viết caption (10 rules bắt buộc)

1. Ngôi thứ nhất: "mình", không dùng "tôi" hay "chúng ta"
2. Mở bài bằng câu chuyện cá nhân 3-4 câu, tình huống cụ thể, cảm xúc thật
3. Dùng "các mẹ", "mẹ ơi" — không dùng "bạn"
4. **CẤM:** "giai đoạn này", "vượt bậc", "tuyệt vời", "khám phá", "hãy cùng", "đừng bỏ lỡ", "người bạn đồng hành", "lột xác", "chuyển mình lớn lao", "dung hòa cảm xúc"
5. Nhắc tên Bơ ít nhất 2 lần
6. Kết bằng câu hỏi mở cụ thể (không hỏi chung chung)
7. Độ dài 150-250 từ, không quá 300 từ
8. Bullet point tối đa 3 cái; bài kể chuyện không dùng bullet
9. Hashtag không dấu tiếng Việt, bắt buộc có **#MeKheoConKhoe**
10. Lồng ghép tự nhiên 1 câu liên quan sản phẩm an toàn/tiện ích cho bé

**Giọng văn:** Văn nói, câu ngắn, chấm lửng..., emoji cảm xúc, chi tiết cụ thể thân xác ("bụng nhão", "rụng tóc", "ngực căng tức"). Mẹ bỉm ở Kon Tum, Hà Giang, Cần Thơ đọc phải relate ngay.

**Thuật ngữ phương Tây:** PHẢI Việt hóa — không dùng "matrescence", "sleep regression", "wonder weeks"... Đổi thành cách nói thông thường.

## Tự động hàng ngày (GitHub Actions)

Repo: `github.com/sn010698c-png/thebump-autopost`

Lịch chạy:
- **8:00 sáng** giờ VN (01:00 UTC)
- **5:00 chiều** giờ VN (10:00 UTC)

Sau mỗi lần chạy, `state.json` tự động commit về repo để tránh đăng bài trùng.

**Secrets cần thiết trên GitHub** (Settings → Secrets and variables → Actions):
`GEMINI_API_KEY`, `FB_PAGE_TOKEN`, `FB_PAGE_ID`, `FB_APP_ID`, `FB_APP_SECRET`, `FB_USER_TOKEN`, `BO_AGE`

**Chạy thủ công:** Vào tab Actions → Daily Facebook Autopost → Run workflow

## Facebook Token

Flow: Short-lived User Token (1h) → Long-lived User Token (60 ngày) → Page Token (không hết hạn)

- `main.py` tự gọi `should_refresh()` mỗi ngày, tự động refresh nếu token < 7 ngày
- Refresh thủ công: `PYTHONUTF8=1 python refresh_token.py "TOKEN_MỚI"`
- Lấy User Token mới tại: developers.facebook.com → Graph API Explorer

## Chạy thủ công (local)

```bash
# Chạy full flow
PYTHONUTF8=1 python main.py

# Test từng module
PYTHONUTF8=1 python scraper.py
PYTHONUTF8=1 python ai_processor.py
PYTHONUTF8=1 python facebook_poster.py

# Refresh token thủ công
PYTHONUTF8=1 python refresh_token.py "USER_TOKEN_MỚI"
```

> Windows cần `PYTHONUTF8=1` để tránh lỗi encoding tiếng Việt.

## Cài đặt lại từ đầu

```bash
pip install -r requirements.txt
cp .env.example .env
# Điền API keys + BO_AGE vào .env
```

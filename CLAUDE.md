# thebump-autopost

Script Python tự động scrape bài từ thebump.com, dùng Gemini AI tạo caption tiếng Việt + ảnh minh hoạ, rồi đăng lên Facebook Page mỗi ngày.

## Flow

```
Google News RSS (thebump.com) → Gemini AI → Facebook Graph API
```

1. `scraper.py` – Lấy bài mới từ Google News RSS (thebump.com bị Akamai chặn scrape trực tiếp)
2. `ai_processor.py` – Gemini tạo caption tiếng Việt + ảnh minh hoạ
3. `facebook_poster.py` – Đăng ảnh + caption lên Facebook Page qua Graph API
4. `main.py` – Orchestrator, chạy toàn bộ flow + log + lưu ảnh

## Cấu trúc thư mục

```
thebump-autopost/
├── main.py               # Entry point
├── scraper.py            # Google News RSS scraper
├── ai_processor.py       # Gemini: caption TV + image gen
├── facebook_poster.py    # Facebook Graph API v19.0
├── .env                  # API keys (không commit)
├── state.json            # URL đã đăng (tránh trùng)
├── images/
│   └── YYYY-MM-DD/       # Ảnh AI tạo, lưu theo ngày
├── logs/
│   └── run.log           # Log mỗi lần chạy
├── requirements.txt
└── setup_scheduler.bat   # Đăng ký Windows Task Scheduler
```

## Cấu hình (.env)

```
GEMINI_API_KEY=     # aistudio.google.com/apikey
FB_PAGE_TOKEN=      # Page Access Token (KHÔNG phải User Token)
FB_PAGE_ID=         # ID của Facebook Page
```

**Lưu ý quan trọng:**
- `FB_PAGE_TOKEN` phải là **Page Token**, lấy qua `GET /me/accounts` từ User Token
- Token Graph API Explorer mặc định là User Token → sẽ bị lỗi `publish_actions`

## Facebook Page

- **Tên:** Mẹ Khéo Con Khoẻ
- **ID:** 166281259901889

## Models Gemini

- **Text:** `gemini-2.5-flash`
- **Image:** `gemini-2.5-flash-image`

## Chạy thủ công

```bash
# Chạy full flow
PYTHONUTF8=1 python main.py

# Test từng module
PYTHONUTF8=1 python scraper.py
PYTHONUTF8=1 python ai_processor.py
PYTHONUTF8=1 python facebook_poster.py
```

> Windows cần thêm `PYTHONUTF8=1` để tránh lỗi encoding tiếng Việt.

## Tự động hàng ngày

Task Scheduler Windows, task tên **ThebumpAutopost**, chạy lúc **8:00 sáng** mỗi ngày.

```bash
# Xem trạng thái task
powershell -Command "schtasks /query /tn 'ThebumpAutopost' /fo LIST"

# Chạy thử ngay
powershell -Command "schtasks /run /tn 'ThebumpAutopost'"

# Xoá task
powershell -Command "schtasks /delete /tn 'ThebumpAutopost' /f"
```

> Máy tính cần **bật và đăng nhập** thì task mới chạy được.

## Cài đặt lại từ đầu

```bash
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
# Điền API keys vào .env
setup_scheduler.bat
```

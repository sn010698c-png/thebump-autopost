# thebump-autopost → Nguyên Học AI

Script Python tự động scrape bài từ nhiều nguồn AI/công nghệ quốc tế uy tín
(OpenAI, Anthropic, Google DeepMind, TechCrunch, The Verge, Zapier...), dùng
OpenAI tạo caption tiếng Việt (giọng "Nguyên" — người thật chia sẻ cách dùng AI)
+ ảnh minh hoạ, rồi đăng lên Facebook Page **"Nguyên Học AI"** mỗi ngày 2 lần
(8h sáng + 5h chiều).

> Ghi chú: tên repo/thư mục vẫn là `thebump-autopost` (di sản từ dự án cũ về
> chủ đề mẹ & bé). Nội dung đã pivot hoàn toàn sang AI/công nghệ.

## Flow

```
RSS/Atom nhiều nguồn AI + Google News → OpenAI → Facebook Graph API
```

1. `scraper.py` – Lấy bài từ ~20 nguồn RSS/Atom về AI/công nghệ
2. `ai_processor.py` – OpenAI tạo caption tiếng Việt (giọng Nguyên) + ảnh minh hoạ
3. `facebook_poster.py` – Đăng ảnh + caption lên Facebook Page qua Graph API
4. `main.py` – Orchestrator: token check → scrape → AI → lưu ảnh → đăng FB → log
5. `refresh_token.py` – Tự động làm mới Facebook token

## Cấu trúc thư mục

```
thebump-autopost/
├── main.py               # Entry point
├── scraper.py            # Multi-source RSS/Atom scraper (AI/công nghệ)
├── ai_processor.py       # OpenAI: caption TV giọng Nguyên + image gen
├── skill_content.md      # Bộ rule viết content (nạp làm system prompt)
├── facebook_poster.py    # Facebook Graph API v19.0
├── refresh_token.py      # Tự động refresh Facebook token
├── .env                  # API keys + config (không commit)
├── state.json            # URL đã đăng (tránh trùng) + trạng thái luân phiên loại bài
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
OPENAI_API_KEY=     # platform.openai.com/api-keys
FB_PAGE_TOKEN=      # Page Access Token của page "Nguyên Học AI" (KHÔNG phải User Token)
FB_PAGE_ID=         # ID của Facebook Page "Nguyên Học AI"
FB_APP_ID=          # App ID từ Meta for Developers
FB_APP_SECRET=      # App Secret từ Meta for Developers
FB_USER_TOKEN=      # Long-lived User Token (60 ngày)
```

**Lưu ý quan trọng:**
- `FB_PAGE_TOKEN` phải là **Page Token**, lấy qua `GET /me/accounts` từ User Token
- Biến `BO_AGE` của dự án cũ đã bỏ, không còn dùng

## Facebook Page

- **Tên:** Nguyên Học AI
- **ID:** _cần cập nhật ID page mới vào `.env` và secret GitHub_

## Models OpenAI

- **Text:** `gpt-5.4-mini`
- **Image:** `gpt-image-2`

## Nguồn crawl (scraper.py)

~17 feed RSS/Atom trực tiếp + 3 truy vấn Google News (cho lab không có RSS chính chủ).
Tất cả đã được kiểm tra sống.

| Nhóm | Nguồn |
|---|---|
| 📰 Tin AI/công nghệ | MIT Tech Review, The Verge, Ars Technica, TechCrunch AI, VentureBeat AI, Wired AI, The Register, AI News, MarkTechPost |
| 🏢 Blog lab AI (nguồn gốc) | OpenAI, Google AI, Google DeepMind, Hugging Face, Mistral AI |
| 🛠️ Thực hành / how-to | Zapier, Simon Willison, Tom's Guide |
| 🔁 Google News fallback | Anthropic (`site:anthropic.com`), Meta AI (`site:ai.meta.com`), Microsoft Copilot |

**Cơ chế scraper:**
- Parse được **cả RSS 2.0 lẫn Atom** (link nằm ở text hoặc attribute `href`)
- Feed chuyên AI (`ai_feed`) lấy hết bài; feed tổng hợp phải trúng **bộ lọc keyword AI/công nghệ** (`_RELEVANT`) mới lấy → loại bài lạc đề (xe cộ, phim ảnh...)
- Giới hạn tối đa 2 bài/nguồn/lần + shuffle thứ tự nguồn mỗi lần chạy → nội dung đa dạng
- Dedup theo URL (đã lưu trong `state.json`)

**4 category** (scraper tự gán từ nguồn + tinh chỉnh theo keyword title):
`ai_news` · `ai_howto` · `ai_tools` · `tech`

## Content Logic (quan trọng)

**Nhân vật:** **Nguyên** — người Việt mê công nghệ, tự học và dùng AI mỗi ngày,
kể lại trải nghiệm thật bằng ngôn ngữ dễ hiểu. Xưng "mình", gọi người đọc là
"cả nhà" / "mọi người".

**Định vị page giai đoạn này: BUILD CỘNG ĐỒNG.**
- KHÔNG bán hàng, KHÔNG chèn sản phẩm, KHÔNG báo giá
- Chỉ cho giá trị (mẹo, hướng dẫn, tin dễ hiểu) → kéo follow + tương tác

**Góc viết theo category:**
- `ai_news` → giải thích tin dễ hiểu, luôn nói *ảnh hưởng gì tới người dùng thường*
- `ai_howto` → hướng dẫn từng bước, có ví dụ prompt copy làm theo được ngay
- `ai_tools` → review trung thực, cái nào hợp việc gì
- `tech` → tin công nghệ liên hệ đời sống người Việt

**Nội dung chi tiết:** xem `skill_content.md` (được nạp làm system prompt cho OpenAI).

## Rules viết caption (tóm tắt — chi tiết trong skill_content.md)

1. Ngôi thứ nhất "mình", KHÔNG "tôi"/"chúng ta"; gọi người đọc "cả nhà"/"mọi người"
2. Hook 2–3 câu đầu có tình huống/kết quả bất ngờ + emoji
3. **Giải thích thuật ngữ AI khó** ngay bằng tiếng Việt dễ hiểu (prompt, LLM, agent, hallucinate...) — giữ tên riêng (ChatGPT, Gemini, Claude)
4. **CẤM:** "vượt bậc", "tuyệt vời", "khám phá", "hãy cùng", "đừng bỏ lỡ", "giai đoạn này", "cuộc cách mạng công nghệ", "thay đổi cuộc chơi", "bùng nổ", "đột phá", "kỷ nguyên mới", giật tít quá đà
5. Cho ít nhất 1 điểm giá trị người đọc mang về được (mẹo / ví dụ prompt)
6. KHÔNG bán hàng, KHÔNG chèn sản phẩm
7. Kết bằng câu hỏi mở cụ thể kéo comment
8. Độ dài 150–250 từ
9. Hashtag không dấu, bắt buộc có **#NguyenHocAI**
10. Bullet tối đa 3 (chỉ khi là các bước); bài kể chuyện không dùng bullet

**Giọng văn:** Văn nói, câu ngắn, xuống dòng nhiều, emoji vừa phải, gần gũi như
người đi trước chia sẻ lại — KHÔNG dạy đời, KHÔNG ra vẻ chuyên gia.

**5 loại bài luân phiên (A→E):** trải nghiệm cá nhân · mẹo/hướng dẫn ·
tương tác/câu hỏi · góc nhìn/cảnh báo · tin nóng+bình luận.
(Luân phiên tự động qua `last_loai_bai_idx` trong `state.json`.)

## Tự động hàng ngày (GitHub Actions)

Repo: `github.com/sn010698c-png/thebump-autopost`

Lịch chạy:
- **8:00 sáng** giờ VN (01:00 UTC)
- **5:00 chiều** giờ VN (10:00 UTC)

Sau mỗi lần chạy, `state.json` tự động commit về repo để tránh đăng bài trùng.

**Secrets cần thiết trên GitHub** (Settings → Secrets and variables → Actions):
`OPENAI_API_KEY`, `FB_PAGE_TOKEN`, `FB_PAGE_ID`, `FB_APP_ID`, `FB_APP_SECRET`, `FB_USER_TOKEN`
(secret `BO_AGE` của dự án cũ có thể xoá.)

**Chạy thủ công:** Vào tab Actions → chọn workflow → Run workflow

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
PYTHONUTF8=1 python scraper.py         # in ra các bài scrape được
PYTHONUTF8=1 python ai_processor.py    # test caption + ảnh 1 bài mẫu
PYTHONUTF8=1 python facebook_poster.py

# Refresh token thủ công
PYTHONUTF8=1 python refresh_token.py "USER_TOKEN_MỚI"
```

> Windows cần `PYTHONUTF8=1` để tránh lỗi encoding tiếng Việt.

## Cài đặt lại từ đầu

```bash
pip install -r requirements.txt
cp .env.example .env
# Điền API keys vào .env
```

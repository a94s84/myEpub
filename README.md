# 半夏小說網EPUB轉換器 

這是一個基於 FastAPI 的線上應用，輸入半夏小說網站(https://www.banxia.cc)連結，一鍵轉換為 EPUB 檔案，並選擇下載或寄送至 Email。

👉 [線上試用](https://myepub-2.onrender.com/)

---

## 功能特色

-  自動抓取小說章節
-  轉換成 EPUB 電子書格式
-  支援寄送 EPUB 到 Email
-  可上傳自訂封面圖

---

## 技術

- FastAPI
- BeautifulSoup（網頁爬蟲）
- ebooklib（EPUB 產生器）
- SMTP 寄信
- Render 雲端部署

---

## 📦 安裝與執行（開發模式）

```bash
git clone https://github.com/a94s84/myEpub.git
cd your-repo
pip install -r requirements.txt
uvicorn main:app --reload

需要例外建立 .env 檔案：
EMAIL_USER=your@email.com
EMAIL_PASSWORD=your_app_password

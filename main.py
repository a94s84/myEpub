from fastapi import FastAPI, Request, Form, UploadFile, File, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from send_email import send_epub_to_email
from epub_converter import generate_epub
from urllib.parse import quote
import shutil, os, uuid

app = FastAPI()

# Setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DEFAULT_EMAIL = "you@example.com"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/crawl")
async def crawl(
    request: Request,
    url: str = Form(...),
    mode: str = Form(...),
    title: str = Form(""),
    author: str = Form(""),
    cover_image: UploadFile = File(None),
    delivery: str = Form("download"),
    email: str = Form("")
):
    # 處理封面
    cover_path = None
    if cover_image:
        cover_path = os.path.join("static", f"{uuid.uuid4()}_{cover_image.filename}")
        with open(cover_path, "wb") as f:
            shutil.copyfileobj(cover_image.file, f)

    # 檔名預設為書名或 UUID
    safe_name = title or f"book_{uuid.uuid4().hex[:8]}"

    try:
        output_file = generate_epub(
            entry_url=url,
            mode=mode,
            custom_title=title,
            custom_author=author,
            custom_cover_path=cover_path
        )

        if delivery == "email":
            send_epub_to_email(output_file, email or DEFAULT_EMAIL)
            # 清檔案
            if os.path.exists(output_file):
                os.remove(output_file)
            if cover_path and os.path.exists(cover_path):
                os.remove(cover_path)
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": f"✅ 已寄出 EPUB 給 {email or DEFAULT_EMAIL}"
            })

        # 檔案下載
        return JSONResponse({"message": "轉換成功", "filename": output_file})
        
    except Exception as e:
        if os.path.exists(output_file):
            os.remove(output_file)
        if cover_path and os.path.exists(cover_path):
            os.remove(cover_path)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": f"❌ 發生錯誤：{e}"
        })
    
@app.get("/download")
async def download_epub(filename: str = Query(...)):
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="檔案不存在")

    file_stream = open(filename, "rb")
    encoded_filename = quote(os.path.basename(filename))
    response = StreamingResponse(file_stream, media_type="application/epub+zip")
    response.headers["Content-Disposition"] = (
        f"attachment; filename={encoded_filename}; filename*=UTF-8''{encoded_filename}"
    )
    return response
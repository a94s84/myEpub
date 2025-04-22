import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_epub_to_email(epub_path: str, recipient_email: str):
    """從檔案名稱自動取得書名並寄送 EPUB 到 Email"""

    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"找不到檔案：{epub_path}")

    book_title = os.path.splitext(os.path.basename(epub_path))[0]

    # 寄件人設定
    sender_email = os.getenv("EMAIL_USER")
    sender_password =  os.getenv("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        raise EnvironmentError("未設定 EMAIL_USER 或 EMAIL_PASS，請確認 .env 檔案")

    msg = EmailMessage()
    msg["Subject"] = f"您的電子書：{book_title}"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(f"您好，這是您請求的電子書《{book_title}》。請查收附件。")

    # 加入附件
    with open(epub_path, "rb") as f:
        epub_data = f.read()
        msg.add_attachment(
            epub_data,
            maintype="application",
            subtype="epub+zip",
            filename=os.path.basename(epub_path)
        )

    # 發送郵件
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print(f"已寄出《{book_title}》到 {recipient_email}")
    except Exception as e:
        print(f"Email 寄送失敗：{e}")
        raise

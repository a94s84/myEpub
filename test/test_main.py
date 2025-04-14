from fastapi.testclient import TestClient
import pytest
from main import app
import os
import shutil
from pathlib import Path
from fastapi.responses import StreamingResponse
from urllib.parse import quote
import tempfile

client = TestClient(app)

def setup_module(module):
    """Setup any state specific to the execution of the given module."""
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)

def teardown_module(module):
    """Teardown any state that was previously setup with a setup_module method."""
    # Clean up any files in static directory
    if os.path.exists("static"):
        for file in os.listdir("static"):
            file_path = os.path.join("static", file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error: {e}")

def test_read_main():
    """Test the main page endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_crawl_download():
    """Test the crawl endpoint with download option."""
    test_data = {
        "url": "https://www.banxia.cc/books/342486.html",
        "mode": "",
        "title": "",
        "author": "",
        "delivery": "download",
        "email": ""
    }
    
    # Create a test image file for cover
    test_image_path = Path("test_cover.jpg")
    test_image_path.write_bytes(b"fake image content")
    
    with open(test_image_path, "rb") as f:
        files = {
            "cover_image": ("test_cover.jpg", f, "image/jpeg")
        }
        response = client.post("/crawl", data=test_data, files=files)
    
    # Clean up test image
    test_image_path.unlink()
        # 輸出返回的內容類型和狀態碼
    print(response.status_code)
    print(response.headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/epub+zip"
    assert "content-disposition" in response.headers

def test_crawl_email():
    """Test the crawl endpoint with email delivery option."""
    test_data = {
        "url": "https://www.banxia.cc/books/342486.html",
        "mode": "auto",
        "title": "",
        "author": "",
        "delivery": "email",
        "email": "test@gmail.com"
    }
    
    response = client.post("/crawl", data=test_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_crawl_error_handling():
    """Test error handling in crawl endpoint."""
    test_data = {
        "url": "https://www.banxia.cc/books/342486.html",
        "mode": "auto",
        "title": "",
        "author": "",
        "delivery": "download",
        "email": ""
    }
    
    response = client.post("/crawl", data=test_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"] 
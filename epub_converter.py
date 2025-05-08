import os
import re
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ebooklib import epub


def fetch_intro_page(base_url):
    headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
    }
    response = requests.get(base_url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 書名
    title_tag = soup.select_one('.book-describe h1')
    title = title_tag.get_text(strip=True) if title_tag else "未命名書籍"

    # 作者
    author = "未知作者"
    for p in soup.select('.book-describe p'):
        if "作者" in p.get_text():
            author_tag = p.find('a')
            if author_tag:
                author = author_tag.get_text(strip=True)
            break

    # 作品簡介 HTML
    description = soup.find('div', class_='describe-html')
    description_html = str(description) if description else ""

    # 封面圖（data-original）
    cover_img_tag = soup.select_one('div.book-img img')
    cover_url = cover_img_tag.get('data-original') if cover_img_tag else None
    cover_url = urljoin(base_url, cover_url) if cover_url else None

    # 第一章連結
    first_chapter_link = soup.select_one('div.book-list ul li a')
    first_chapter_url = urljoin(base_url, first_chapter_link['href']) if first_chapter_link else None
    return {
        'title': title,
        'author': author,
        'description_html': description_html,
        'cover_url': cover_url,
        'first_chapter_url': first_chapter_url
    }

def fetch_content(start_url):
    chapters = []
    url = start_url
    while url:
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        chapter_title_tag = soup.find('h1', id="nr_title")
        chapter_title = chapter_title_tag.get_text(strip=True) if chapter_title_tag else "未命名章節"

        content_div = soup.find('div', id='nr1')

        if content_div:
            pattern = re.compile(r"本站無彈出廣告，永久域名（ xbanxia\.com ）")
            for tag in content_div.find_all(string=pattern):
                tag.extract()
            content_div['style'] = "font-size: 14px;"
            content_html = "".join(str(child) for child in content_div.contents)
        else:
            content_html = ""


        chapter = epub.EpubHtml(title=chapter_title, file_name=f"{len(chapters)}.xhtml", lang='zh')
        chapter.content = f"""
            <h2>{chapter_title}</h2>
            {content_html}
        """
        chapters.append(chapter)

        next_link_tag = soup.find('a', id='next_url')
        if next_link_tag and 'href' in next_link_tag.attrs:
            url = urljoin(url, next_link_tag['href'])
        else:
            print("📘 沒有下一頁，爬蟲完成")
            break
    return chapters

def generate_epub(entry_url, mode="auto", custom_title="", custom_author="", custom_cover_path=None):
    """
    建立 EPUB 並回傳實際產出的檔名
    """
    intro_data = fetch_intro_page(entry_url)
    if mode == "manual":
        intro_data["title"] = custom_title or intro_data.get("title")
        intro_data["author"] = custom_author or intro_data.get("author")
        intro_data["cover_url"] = custom_cover_path or intro_data.get("cover_url")

    title = intro_data.get("title")
    author = intro_data.get("author")
    description_html = intro_data.get("description_html", "")
    first_chapter_url = intro_data.get("first_chapter_url", "")
    cover_url = intro_data.get("cover_url", "")

    output_filename = f"{title}.epub"

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('zh')
    book.add_author(author)

    # 封面處理
    if cover_url:
        cover_data = requests.get(cover_url).content
        book.set_cover("cover.jpg",cover_data)

    # 作品簡介頁
    intro_chapter = epub.EpubHtml(title="作品簡介", file_name="intro.xhtml", lang="zh")
    intro_chapter.content = f"""
        <h1>{title}</h1>
        <p><strong>作者：</strong>{author}</p>
        {description_html}
    """
    book.add_item(intro_chapter)

    chapters = fetch_content(first_chapter_url)
    for ch in chapters:
        book.add_item(ch)

    book.toc = [epub.Link(ch.file_name, ch.title, f"chap{idx}") for idx, ch in enumerate(chapters, 1)]
    book.spine = ['nav', intro_chapter] + chapters

    book.add_item(epub.EpubNcx())
   
    epub.write_epub(output_filename, book)
    print(f"🎉 EPUB 檔案已完成：{output_filename}")
    return output_filename

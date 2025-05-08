import os
import re
import uuid
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ebooklib import epub

# 建立全域的 scraper（避免每次都建立）
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)


def fetch_intro_page(base_url):
    try:
        response = scraper.get(base_url, timeout=10)
        response.encoding = 'utf-8'

        print("intro HTML 頭部預覽：", response.text[:300])
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

        # 封面圖
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
    except Exception as e:
        print(f"抓取 intro 頁失敗：{e}")
        return {
            'title': '失敗',
            'author': '失敗',
            'description_html': '',
            'cover_url': '',
            'first_chapter_url': ''
        }


def fetch_content(start_url):
    chapters = []
    url = start_url
    while url:
        try:
            res = scraper.get(url, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')

            chapter_title_tag = soup.find('h1', id="nr_title")
            chapter_title = chapter_title_tag.get_text(strip=True) if chapter_title_tag else "未命名章節"

            content_div = soup.find('div', id='nr1')

            if content_div:
                pattern = re.compile(r"本站無彈出廣告，永久域名（ ?xbanxia\.com ?）")
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
                print("沒有下一頁，爬蟲完成")
                break
        except Exception as e:
            print(f"抓取章節錯誤：{e}")
            break

    return chapters


def generate_epub(entry_url, mode="auto", custom_title="", custom_author="", custom_cover_path=None):
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
    cover_data = None
    if cover_url:
        try:
            res = scraper.get(cover_url, timeout=10)
            if res.status_code == 200:
                cover_data = res.content
                book.set_cover("cover.jpg", cover_data)
        except Exception as e:
            print(f"下載封面失敗：{e}")

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
    print(f"EPUB 檔案已完成：{output_filename}")
    return output_filename

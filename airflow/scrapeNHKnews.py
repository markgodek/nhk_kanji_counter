from bs4 import BeautifulSoup
import requests
import neologdn

from load_mongo import load_mongo
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from datetime import datetime

debug = False
homepage = 'https://www3.nhk.or.jp/news/'

#site map for news articles of the last 3 days
#probably a smarter way to pull the links
#https://www3.nhk.or.jp/news/sitemap-news-flow-3days.xml

# a function which takes a URL and returns the parsed text in an object
def get_response(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # force utf-8 for Japanese text
    return BeautifulSoup(response.text, 'html.parser')

def list_articles(homepage):
    soup = get_response(homepage)
    articles = []

    for a in soup.find_all('a'):
        title_tag = a.find('em', class_='title')
        if title_tag:
            tag_text = title_tag.get_text(strip=True)
            normalized_text = neologdn.normalize(tag_text)
            href = a.get('href')
            full_url = urljoin(homepage, href)
            articles.append([normalized_text, full_url])
    return articles

#scrape this using playwright - https://www.nhk.or.jp/senkyo/shijiritsu/
def scrape_with_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www3.nhk.or.jp/news/")
        content = page.content()
        browser.close()
        return content  # or parse + return structured data

def extract_text(articles):
    content = []

    for article in articles:
        url = article[1]
        soup = get_response(url)

        # Remove hidden or irrelevant elements
        for selector in ['[aria-hidden="true"]', '[style*="display:none"]', '.hidden', 'script', 'style', 'noscript']:
            for tag in soup.select(selector):
                tag.decompose()

        # Attempt to find known main content sections
        section_to_use = (
            soup.find('section', class_='module--detail-content') or
            soup.find('section', class_='detail-no-js')
        )

        article_title = ''
        article_datetime = None

        if section_to_use:
            time_tag = section_to_use.find('time')
            article_datetime = time_tag.get('datetime') if time_tag and time_tag.has_attr('datetime') else None

            for tag in section_to_use.find_all(True):
                tag_text = ''.join(tag.find_all(string=True, recursive=False)).strip()
                normalized_text = neologdn.normalize(tag_text)

                if normalized_text:
                    class_ = ' '.join(tag.get('class')) if tag.has_attr('class') else None
                    parent = tag.find_parent(attrs={'class': True})
                    parent_class = ' '.join(parent.get('class')) if parent else None

                    if parent_class == 'content--title' or class_ == 'contentTitle':
                        article_title = normalized_text

                    content.append({
                        'article_title': article_title,
                        'published': article_datetime,
                        'text': normalized_text,
                        'tag': tag.name,
                        'class': class_,
                        'parent_class': parent_class,
                        'url': url,
                        'scraped_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    })
        else:
            # Fallback: scrape all visible text nodes from soup.body
            if soup.body:
                for string in soup.body.find_all(string=True):
                    text = string.strip()
                    if text:
                        normalized_text = neologdn.normalize(text)
                        parent = string.parent
                        tag_name = parent.name if parent else None
                        class_ = ' '.join(parent.get('class')) if parent and parent.has_attr('class') else None
                        parent_class = ' '.join(parent.find_parent().get('class')) if parent and parent.find_parent() and parent.find_parent().has_attr('class') else None

                        content.append({
                            'article_title': None,
                            'published': None,
                            'text': normalized_text,
                            'tag': tag_name,
                            'class': class_,
                            'parent_class': parent_class,
                            'url': url,
                            'scraped_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                        })
    return content


def scrape_NHK():
    articles = list_articles(homepage)
    content = extract_text(articles)
    load_mongo(content)

if __name__ == "__main__":
    scrape_NHK()
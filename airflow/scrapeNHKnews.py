import os, requests, neologdn

from load_mongo import load_mongo
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone

PLAYWRIGHT_HOST = os.getenv("PLAYWRIGHT_HOST", "localhost")
homepage = 'https://www3.nhk.or.jp/news/'

#site map for news articles of the last 3 days
#probably a smarter way to pull the links
#https://www3.nhk.or.jp/news/sitemap-news-flow-3days.xml

# a function which takes a URL and returns the parsed text in an object
def get_response(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    response.encoding = 'utf-8'  # force utf-8 for Japanese text
    return BeautifulSoup(response.text, 'html.parser')

# list articles on homepage
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
def scrape_with_playwright(url):
    try:
        response = requests.post(f"http://{PLAYWRIGHT_HOST}:5010/scrape", json={"url": url}, timeout=30)

        response.raise_for_status()
        return response.json()  # list of dicts with 'text', 'tag', etc.
    except Exception as e:
        print(f"[!] Playwright fallback failed scraping {url}: {e}")
        return []

# takes a url and returns a content object with content scraped using beautiful soup
# if the page lacks tags found in section_to_use, function falls back to scraping with scrape_with_playwright
def scrape_article(url):
    content = []
    article_title = ''
    article_datetime = None

    soup = get_response(url)

    # Attempt to find known main content sections
    candidates = [
        soup.find('section', class_='module--detail-content'),
        soup.find('section', class_='detail-no-js'),
    ]

    section_to_use = next((sec for sec in candidates if sec), None)

    # if the soup has viable content section, scrape with beautifulsoup
    if section_to_use:
        # Remove hidden or irrelevant elements
        for selector in ['[aria-hidden="true"]', '[style*="display:none"]', '.hidden', 'script', 'style', 'noscript']:
            for tag in soup.select(selector):
                tag.decompose()

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
        # fallback to using playwright service for pages with javascript
        content = scrape_with_playwright(url)

    return content

def extract_text(articles):
    content = []

    for article in articles:
        url = article[1]
        content.extend(scrape_article(url))
    return content

def main():
    articles = list_articles(homepage)
    content = extract_text(articles)
    load_mongo(content)

if __name__ == "__main__":
    main()



    if False:
        urls = ['https://www3.nhk.or.jp/news/html/20250612/k10014832631000.html', # normal article - module--detail-content
                'https://www3.nhk.or.jp/news/html/20250610/k10014829951000.html', # WEB 特集 - detail-no-js
                'https://www.nhk.or.jp/senkyo/shijiritsu/'] # 支持率 - portions rendered with Javascript
        content = scrape_article('https://www.nhk.or.jp/senkyo/shijiritsu/')
        # print(content)
        for x in content:
            print(x)
        for url in urls:
            content = scrape_article(url)
            for x in content:
                print(x)

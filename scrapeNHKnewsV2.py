from bs4 import BeautifulSoup
import requests
import neologdn

#from load_mongo import load_mongo
from urllib.parse import urljoin
from datetime import datetime, timezone
from fallback_to_playwright import fallback_to_playwright

debug = False
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


def scrape_with_beautifulsoup(url, soup):
    content = []
    article_title = ''

    # Remove hidden or irrelevant elements
    for selector in ['[aria-hidden="true"]', '[style*="display:none"]', '.hidden', 'script', 'style', 'noscript']:
        for tag in soup.select(selector):
            tag.decompose()

    # Get the date of publication
    time_tag = soup.find('time')
    if time_tag and time_tag.has_attr('datetime'):
        try:
            parsed_dt = datetime.fromisoformat(time_tag['datetime'])
            article_datetime = parsed_dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            article_datetime = None
    else:
        article_datetime = None

    # Get article text and normalize it
    for tag in soup.find_all(True):
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
                'scraped_at': datetime.now(timezone.utc).isoformat()
            })
    return content

def extract_text(articles):
    content = []

    for article in articles:
        url = article[1]

        try:
            # Look at page source
            soup = get_response(url)

            content_container = soup.select_one('[class*="module--detail-content"], [class*="detail-no-js"]')

            # If the tags are present in source
           # if soup.select_one('.module--detail-content, .detail-no-js'):
           #     print("   Required tags found in source. Static scraping. - ", url)
           #     content.append(scrape_with_beautifulsoup(url, soup))
           #else:
           #    print("   Required tags not found in source. Rendered scraping - ", url)
           #     content.append(fallback_to_playwright(url))

            if content_container:
                print("   Required tags found in source. Static scraping. - ", url)
                article_data = scrape_with_beautifulsoup(url, soup)
                content.append(article_data)
            else:
                # Fallback to Playwright if no static container is found
                print(f"   Info: No static container found. Falling back to Playwright for {url}")
                article_data = fallback_to_playwright(url) # This function should return data in the same format
                if article_data:
                    content.append(article_data)

        except requests.exceptions.RequestException as e:
            print(f"   Could not fetch URL {url}. Error: {e}")
        except Exception as e:
            print(f"   An unexpected error occurred: {e}")

    return content

def scrape_NHK():
    articles = list_articles(homepage)
    content = extract_text(articles)
    for x in content:
        for y in x:
            print(y)
    #load_mongo(content)

if __name__ == "__main__":
    scrape_NHK()
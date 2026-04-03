import os, requests, neologdn, hashlib
from load_mongo import load_mongo
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PLAYWRIGHT_HOST = os.getenv("PLAYWRIGHT_HOST", "localhost")
homepage = 'https://news.web.nhk/newsweb'


def get_html_via_playwright(url):
    try:
        response = requests.post(f"http://{PLAYWRIGHT_HOST}:5010/html", json={"url": url}, timeout=60)
        response.raise_for_status()
        html_content = response.json().get("html", "")
        return BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        print(f"[!] Playwright HTML fetch failed for {url}: {e}", flush=True)
        return BeautifulSoup("", 'html.parser')


def list_articles(homepage):
    print(f"Fetching homepage links from {homepage}...", flush=True)
    soup = get_html_via_playwright(homepage)
    articles = []

    all_links = soup.find_all('a', href=True)
    for a in all_links:
        href = a['href']
        if '/newsweb/na/' in href or '/html/' in href:
            strong_tag = a.find('strong')
            if not strong_tag:
                continue

            raw_text = strong_tag.get_text(strip=True)
            normalized_text = neologdn.normalize(raw_text)
            full_url = urljoin(homepage, href)

            if full_url not in [link[1] for link in articles]:
                articles.append([normalized_text, full_url])

    print(f"✅ Found {len(articles)} articles to scrape.", flush=True)
    return articles


def scrape_article(url):
    try:
        response = requests.post(f"http://{PLAYWRIGHT_HOST}:5010/scrape", json={"url": url}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[!] Playwright fallback failed scraping {url}: {e}", flush=True)
        return []


def main():
    articles = list_articles(homepage)

    if not articles:
        print("⚠️ No article links found on homepage. Exiting.", flush=True)
        return

    total = len(articles)
    for i, article in enumerate(articles):
        title = article[0]
        url = article[1]

        # flush=True forces Airflow to update the logs immediately
        print(f"[{i + 1}/{total}] Scraping: {title}", flush=True)

        content = scrape_article(url)

        if content:
            load_mongo(content)
            print(f"  -> Successfully loaded into MongoDB.", flush=True)
        else:
            print(f"  -> ⚠️ No content extracted from this URL.", flush=True)


if __name__ == "__main__":
    pass
import requests
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def get_response(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return response

def scrape_all_text(url):
    response = get_response(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    main = soup.find('main')
    if not main:
        return []

    # Get all text inside main, clean up whitespace, split by lines
    raw_text = main.get_text(separator='\n', strip=True)
    # Filter out empty lines
    lines = [line for line in raw_text.split('\n') if line.strip()]
    return lines

async def scrape_all_text_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        # Wait for main content to load - adjust selector if needed
        await page.wait_for_selector('main')

        # Get all text inside <main>
        content = await page.eval_on_selector('main', 'el => el.innerText')
        await browser.close()
        return content

if __name__ == '__main__':
    url = 'https://www.nhk.or.jp/senkyo/shijiritsu/'
    all_text = scrape_all_text(url)
    for line in all_text:
        print(line)
    print('------------------------------------------------')

    text = asyncio.run(scrape_all_text_playwright(url))
    print(text)

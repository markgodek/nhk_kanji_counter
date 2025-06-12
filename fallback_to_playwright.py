import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timezone
import re


def parse_special_page_date(text):

    # Attempt to match formats like: '2025年6月(6月9日更新)' or full Japanese date strings
    year_match = re.search(r'(\d{4})年', text)
    update_match = re.search(r'(\d{1,2})月(\d{1,2})日更新', text)

    if year_match and update_match:
        year = int(year_match.group(1))
        month = int(update_match.group(1))
        day = int(update_match.group(2))
        dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
        return dt.isoformat()
    else:
        print("Regex did not match. Year:", year_match, "Update:", update_match)
    return None


async def fallback_to_playwright(url):
    content =[]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector('main', timeout=10000)

        full_text = await page.eval_on_selector('main', 'el => el.innerText')
        article_title = await page.title()

        try:
            pub_date_element = await page.query_selector('time')
            publication_date = await pub_date_element.get_attribute('datetime') if pub_date_element else None
        except:
            publication_date = None

        if not publication_date:
            try:
                section = await page.query_selector('section.lead')
                if section:
                    section_text = await section.inner_text()
                    publication_date = parse_special_page_date(section_text)
                else:
                    print("No section.lead found")
            except Exception as e:
                print("Error extracting from section.lead:", e)
                publication_date = None

        scraped_at = datetime.now(timezone.utc).isoformat()
        await browser.close()

        for line in full_text.splitlines():
            if line:
                content.append({
                    "article_title": article_title,
                    "published": publication_date,
                    "text": line,
                    "tag": "main",
                    "class": None,
                    "parent_class": None,
                    "url": url,
                    "scraped_at": scraped_at
                })

        return content

if __name__ == '__main__':
    url = 'https://www.nhk.or.jp/senkyo/shijiritsu/'
    result = asyncio.run(fallback_to_playwright(url))
    for x in result:
        print(x)
    #print(result)


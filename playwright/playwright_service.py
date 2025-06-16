import asyncio, re, json, neologdn, hashlib

from flask import Flask, request, Response
from playwright.async_api import async_playwright
from datetime import datetime, timezone

app = Flask(__name__)

def parse_special_page_date(text):
    year_match = re.search(r'(\d{4})\u5e74', text)
    update_match = re.search(r'(\d{1,2})\u6708(\d{1,2})\u65e5\u66f4\u65b0', text)

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
    content = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector('main', timeout=10000)

        #full_text = await page.eval_on_selector('main', 'el => el.innerText') # scrapes only the text in main
        full_text = await page.evaluate("() => document.body.innerText") # get all text on the page
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
            if line.strip():
                normalized_text = neologdn.normalize(line.strip())
                text_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

                content.append({
                    "article_title": article_title,
                    "published": publication_date,
                    "text": normalized_text,
                    "text_hash": text_hash,
                    "tag": "body",
                    "class": None,
                    "parent_class": None,
                    "url": url,
                    "scraped_at": scraped_at
                })

        return content

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return Response(json.dumps({"error": "Missing 'url' in request body"}), status=400, mimetype='application/json')

    result = asyncio.run(fallback_to_playwright(url))
    return Response(json.dumps(result, ensure_ascii=False), mimetype='application/json')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)

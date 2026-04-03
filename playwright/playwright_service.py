import asyncio, re, json, neologdn, hashlib
from flask import Flask, request, Response
from playwright.async_api import async_playwright
from datetime import datetime, timezone

app = Flask(__name__)


def parse_special_page_date(text):
    year_match = re.search(r'(\d{4})\u5e74', text)
    update_match = re.search(r'(\d{1,2})\u6708(\d{1,2})\u65e5\u66f4\u65b0', text)
    if year_match and update_match:
        return datetime(int(year_match.group(1)), int(update_match.group(1)), int(update_match.group(2)), 12, 0,
                        tzinfo=timezone.utc).isoformat()
    return None


async def dismiss_overseas_modal(page):
    try:
        button = await page.wait_for_selector('button:has-text("I understand")', timeout=3000)
        if button:
            await button.click()
            await page.wait_for_timeout(1000)
    except Exception:
        pass  # Modal not found, safely ignore


async def fetch_rendered_html(url):
    html = ""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                # domcontentloaded is much faster and less prone to timeouts than networkidle
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await dismiss_overseas_modal(page)
                # Wait up to 15 seconds for actual articles to appear
                await page.wait_for_selector('a[href*="/newsweb/na/"]', timeout=15000)
            except Exception as e:
                print(f"[!] Playwright navigation timeout/error (HTML): {e}")

            # Grab whatever HTML rendered, even if it timed out waiting for something else
            html = await page.content()
            await browser.close()
    except Exception as e:
        print(f"[!] Critical browser failure: {e}")

    return {"html": html}


async def fallback_to_playwright(url):
    content = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await dismiss_overseas_modal(page)
                await page.wait_for_timeout(2000)  # Give the SPA a moment to hydrate text
            except Exception as e:
                print(f"[!] Playwright navigation timeout/error (Scrape): {e}")

            # Safely extract elements
            try:
                full_text = await page.evaluate("() => document.body.innerText")
            except Exception:
                full_text = ""

            try:
                article_title = await page.title()
            except Exception:
                article_title = ""

            publication_date = None
            try:
                pub_date_element = await page.query_selector('time')
                if pub_date_element:
                    publication_date = await pub_date_element.get_attribute('datetime')
            except Exception:
                pass

            if not publication_date:
                try:
                    section = await page.query_selector('section.lead')
                    if section:
                        publication_date = parse_special_page_date(await section.inner_text())
                except Exception:
                    pass

            scraped_at = datetime.now(timezone.utc).isoformat()
            await browser.close()

            if full_text:
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
    except Exception as e:
        print(f"[!] Critical browser failure: {e}")

    return content


@app.route("/html", methods=["POST"])
def get_html():
    url = request.get_json().get("url")
    return Response(json.dumps(asyncio.run(fetch_rendered_html(url)), ensure_ascii=False), mimetype='application/json')


@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.get_json().get("url")
    return Response(json.dumps(asyncio.run(fallback_to_playwright(url)), ensure_ascii=False),
                    mimetype='application/json')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import neologdn
from datetime import datetime

app = Flask(__name__)


@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        content = []

        elements = page.locator("body").locator("*")
        count = elements.count()
        for i in range(count):
            el = elements.nth(i)
            try:
                text = el.inner_text(timeout=1000).strip()
                if text:
                    content.append({
                        "text": neologdn.normalize(text),
                        "tag": el.evaluate("e => e.tagName").lower(),
                        "url": url,
                        "scraped_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    })
            except:
                continue

        browser.close()
        return jsonify(content)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)

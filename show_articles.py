from flask import Flask, request, render_template_string, url_for
from common.mongo_connection import get_mongo_client
from pymongo.errors import PyMongoError

app = Flask(__name__)

try:
    mongo_client = get_mongo_client()
except PyMongoError as e:
    print(f"❌ Mongo connection failed: {e}")

db = mongo_client["NHK_articles"]
collection = db["NHK_articles"]

@app.route("/", methods=["GET", "POST"])
def show_articles():
    page = int(request.args.get("page", 1))
    per_page = 20
    skip = (page - 1) * per_page

    total = collection.count_documents({})
    articles = list(collection.find().sort("_id", 1).skip(skip).limit(per_page))

    has_next = skip + per_page < total
    has_prev = page > 1

    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>NHK Raw Articles</title>
        <style>
            body { font-family: sans-serif; margin: 2em; }
            .article { margin-bottom: 2em; padding-bottom: 1em; border-bottom: 1px solid #ddd; }
            .nav-buttons { margin-top: 2em; }
            button {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                margin: 0 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1em;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
    <h1>NHK Raw Articles</h1>
    {% for doc in articles %}
        <div class="article">
            <strong><a href="{{ doc.get('url', '#' ) }}" target="_blank">
                    {{ doc.get('article_title', '[No title]') }}
                </a></strong><br>
            <p>{{ doc.get('text', '[No text]') }}</p>
        </div>
    {% endfor %}

    <div class="nav-buttons">
        <form method="get" style="display: inline;">
            <input type="hidden" name="page" value="{{ page - 1 }}">
            <button type="submit" {% if not has_prev %}disabled{% endif %}>⟵ Previous</button>
        </form>

        <form method="get" style="display: inline;">
            <input type="hidden" name="page" value="{{ page + 1 }}">
            <button type="submit" {% if not has_next %}disabled{% endif %}>Next ⟶</button>
        </form>
    </div>
    </body>
    </html>
    """
    return render_template_string(html, articles=articles, page=page, has_next=has_next, has_prev=has_prev)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

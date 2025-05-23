import os
from pymongo import MongoClient

#input into Docker Desktop to create mongoDB container
#docker run -p 27017:27017 --name NHK-mongo -d mongo

def initialize_mongo(content):
    # Connect to the MongoDB dynamically in container vs debugging locally in PyCharm
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    client = MongoClient(f'mongodb://{mongo_host}:27017')

    # Get or create the database
    db = client['NHK_articles']

    # Get or create the collection
    article_collection = db['NHK_articles']

    result = article_collection.insert_many(content)

    # Now check if the collection exists in the database
    if "NHK_articles" in db.list_collection_names():
        print("Article collection created!")
        print(f"Inserted {len(result.inserted_ids)} documents.")
    else:
        print("Article collection NOT found.")

# if run independently, insert three documents as a test
if __name__ == "__main__":
    content = [{'article_title': 'どう防ぐ海外赴任での過労死・過労自殺遺族たちの声', 'published': '2025-05-22T18:16:48', 'text': 'Q.労災保険の特別加入の制度についてはどう考えますか。', 'tag': 'span', 'class': 'pattern_1', 'parent_class': 'body-text', 'url': 'https://www3.nhk.or.jp/news/html/20250522/k10014813301000.html', 'scraped_at': '2025-05-23T14:52:57'},
            {'article_title': 'どう防ぐ海外赴任での過労死・過労自殺遺族たちの声', 'published': '2025-05-22T18:16:48', 'text': '「海外労働連絡会」について', 'tag': 'h2', 'class': 'body-title', 'parent_class': 'content--body', 'url': 'https://www3.nhk.or.jp/news/html/20250522/k10014813301000.html', 'scraped_at': '2025-05-23T14:52:57'},
            {'article_title': 'どう防ぐ海外赴任での過労死・過労自殺遺族たちの声', 'published': '2025-05-22T18:16:48', 'text': '上田さんが参加する「海外労働連絡会」はホームページで活動の内容について公表しています。https://linjow.org/●厚生労働省は、海外で働く人に向けた労災保険の特別加入についてのしおりを公表しています。https://www.mhlw.go.jp/new-info/kobetu/roudou/gyousei/rousai/040324-7.html●また、厚生労働省は、ホームページなどで不安や悩みを抱える人の相談窓口を紹介しています。インターネットで「まもろうよこころ」で検索することもできます。電話での主な相談窓口「よりそいホットライン」0120-279-338「こころの健康相談統一ダイヤル」0570-064-556', 'tag': 'p', 'class': None, 'parent_class': 'body-text', 'url': 'https://www3.nhk.or.jp/news/html/20250522/k10014813301000.html', 'scraped_at': '2025-05-23T14:52:57'}]

    initialize_mongo(content)
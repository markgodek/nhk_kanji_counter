from pymongo import MongoClient
import os
from pymongo import MongoClient

def get_kanji(mongoDB)
# extract only the kanji
    for article in articles:
        text = article.text
        kanji = re.findall(r'[\u4e00-\u9faf]+', text)
        print(text)
        print(kanji)



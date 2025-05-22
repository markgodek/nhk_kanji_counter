from pymongo import MongoClient
import scrapeNHKnews

#input into Docker Desktop to create mongoDB container
#docker run -p 27017:27017 --name NHK-mongo -d mongo

homepage = 'https://www3.nhk.or.jp/news/'

# make a connection
client = MongoClient('mongodb://localhost:27017')

# get a database
db = client['NHK_articles']

# get collection
article_collection = db.NHK_articles

# get articles
articles = scrapeNHKnews.scrape_NHK(homepage)

result = article_collection.insert_many(articles)

if "article_collection" in client.list_database_names():

    print("Article database created!")

print(result.inserted_ids)
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
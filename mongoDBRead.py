import os
from pymongo import MongoClient

def read_mongo():
    # Connect to the MongoDB dynamically in container vs debugging locally in PyCharm
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    client = MongoClient(f'mongodb://{mongo_host}:27017')

    # get the database
    db = client['NHK_articles']

    # get collection
    collection  = db['NHK_articles']

    # return documents
    return collection.find()

if __name__ == "__main__":
    documents = read_mongo()

    # walk through all posts
    for document in documents:
        print(document)
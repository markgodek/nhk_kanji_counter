from pymongo import MongoClient

# make a connection
client = MongoClient('mongodb://localhost:27017')

# get database
db = client['NHK_articles']

# get collection
documents = db.NHK_articles

# walk through all posts
for document in documents.find():
    print(document)
import os
from pymongo import MongoClient

def get_mongo_client():
    mongo_user = os.getenv('MONGO_USER', 'mongo')
    mongo_pass = os.getenv('MONGO_PASS', 'mongo')
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    return MongoClient(f'mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:27017/')

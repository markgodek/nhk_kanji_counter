import os, re
from pymongo import MongoClient
import mysql.connector
from mysql.connector import errorcode
from bson import ObjectId
from collections import Counter

# constants for SQL database
DB_NAME = 'NHKdb'
METADATA_TABLE = 'metadata'
DATA_TABLE = 'nhk_data'

def get_sql_connection():
    sql_connection = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'MyNewPass',
        database = 'NHKdb',
        port = 3306
    )
    return sql_connection

def get_last_processed_id():
    try:
        # Get the connection from get_sql_connection
        sql_connection = get_sql_connection()

        # Create a cursor using the connection
        cursor = sql_connection.cursor()

        query = """
        SELECT last_processed_id
        FROM metadata
        ORDER BY processed_at DESC
        LIMIT 1;
        """
        cursor.execute(query)
        result = cursor.fetchone()[0]
        return result
    except mysql.connector.Error as err:
        print(f"Database error: {err}")

    finally:
        cursor.close()
        sql_connection.close()

def update_last_processed_id(new_id):
    sql_connection = get_sql_connection()

    try:
        cursor = sql_connection.cursor()
        query = """
        INSERT INTO metadata (last_processed_id) 
        VALUES (%s)
        ON DUPLICATE KEY UPDATE last_processed_id = %s;
        """
        cursor.execute(query, (new_id, new_id))
        sql_connection.commit()
    except mysql.connector.Error as err:
        print(f"Database error while updating: {err}")
    finally:
        cursor.close()
        sql_connection.close()

def get_mongo_client():
    # Connect to the MongoDB dynamically in container vs debugging locally in PyCharm and return client
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    return MongoClient(f'mongodb://{mongo_host}:27017')

def read_mongo():
    mongo_client = get_mongo_client() # get a connection
    db = mongo_client['NHK_articles'] # get the database
    collection = db['NHK_articles'] # get the collection
    return collection.find() # return documents

def count_kanji(document):
    kanji = re.findall(r'[\u4e00-\u9faf]', document['text'])
    return dict(Counter(kanji))

def batch_process():
    mongo_client = get_mongo_client()
    db = mongo_client['NHK_articles']  # Get or create the database
    article_collection = db['NHK_articles'] # Get or create the collection

    # Fetch last processed _id from SQL
    last_processed_id = get_last_processed_id()

    query = {"_id": {"$gt": ObjectId(last_processed_id)}} if last_processed_id else {}
    batch_size = 1000

    while True:
        batch = list(article_collection.find(query).sort("_id", 1).limit(batch_size))
        if not batch:
            print("No more documents to process.")
            break
        print(batch)
        for doc in batch:
            processed = process(doc)
            save_to_sql(processed)

            last_processed_id = str(doc["_id"])

        # Save progress after each batch
        update_last_processed_id(last_processed_id)

        print(f"Batch processed up to {last_processed_id}.")

if __name__ == "__main__":
    documents = read_mongo()

    # walk through all posts
    for document in documents:
        #print(document)
        print(count_kanji(document))


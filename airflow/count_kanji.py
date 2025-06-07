import os, re
from pymongo import MongoClient
import mysql.connector
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

def get_mongo_client():
    # Connect to the MongoDB dynamically in container vs debugging locally in PyCharm and return client
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    return MongoClient(f'mongodb://{mongo_host}:27017')

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
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            pass
    except mysql.connector.Error as err:
        print(f"Database error while getting last processed ID: {err}")

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

def read_mongo():
    mongo_client = get_mongo_client() # get a connection
    db = mongo_client['NHK_articles'] # get the database
    collection = db['NHK_articles'] # get the collection
    return collection.find() # return documents

def count_kanji(document):
    kanji = re.findall(r'[\u4e00-\u9faf]', document['text'])
    return dict(Counter(kanji))

def processx(document):
    # Get the connection from get_sql_connection
    sql_connection = get_sql_connection()
    cursor = sql_connection.cursor()
    kanji_counts = count_kanji(document)
    try:
        query = """
        INSERT INTO kanji_count (kanji, count)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE count = count + %s;
        """

        for kanji, count in kanji_counts.items():
            cursor.execute(query, (kanji, count, count))

        sql_connection.commit() # Commit once per document, not per kanji
    except mysql.connector.Error as err:
        print(f"Database error while updating count: {err}")

def process(document):
    # Get the connection from get_sql_connection
    sql_connection = get_sql_connection()
    cursor = sql_connection.cursor()
    kanji_counts = count_kanji(document)
    try:
        query = """
        INSERT INTO kanji_count (kanji, count)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE count = count + values(count);
        """

        # bulk insert using executemany
        params = [(kanji, count) for kanji, count in kanji_counts.items()]
        cursor.executemany(query, params)

        sql_connection.commit() # Commit once per document, not per kanji
    except mysql.connector.Error as err:
        print(f"Database error while updating count: {err}")

def batch_process():
    mongo_client = get_mongo_client()
    db = mongo_client['NHK_articles']
    article_collection = db['NHK_articles']

    last_processed_id = get_last_processed_id()
    batch_size = 1000
    total_processed = 0

    # Open a single SQL connection for the entire batch
    sql_connection = get_sql_connection()
    cursor = sql_connection.cursor()

    try:
        while True:
            query = {"_id": {"$gt": ObjectId(last_processed_id)}} if last_processed_id else {}
            batch = list(article_collection.find(query).sort("_id", 1).limit(batch_size))

            if not batch:
                print("✅ No more documents to process.")
                break

            # Aggregate all kanji from the batch
            batch_kanji_counter = Counter()
            for document in batch:
                kanji_counts = count_kanji(document)
                batch_kanji_counter.update(kanji_counts)
                last_processed_id = str(document["_id"])
                total_processed += 1

            # Perform one bulk upsert
            query = """
            INSERT INTO kanji_count (kanji, count)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE count = count + VALUES(count);
            """
            params = [(kanji, count) for kanji, count in batch_kanji_counter.items()]
            cursor.executemany(query, params)
            sql_connection.commit()

            # Save progress after each batch
            update_last_processed_id(last_processed_id)
            print(f"✅ Processed {total_processed} documents. Last ID: {last_processed_id}")

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
    finally:
        cursor.close()
        sql_connection.close()
        print(f"🎉 Done! Total documents processed: {total_processed}")

if __name__ == "__main__":
    batch_process()
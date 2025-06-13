import os, re
import mysql.connector

from bson import ObjectId
from collections import Counter
from pymongo.errors import PyMongoError
from common.mongo_connection import get_mongo_client


# constants for SQL database
DB_NAME = 'NHKdb'
METADATA_TABLE = 'metadata'
DATA_TABLE = 'nhk_data'

def get_sql_connection():
    host = os.getenv("MYSQL_HOST", "localhost")

    try:
        sql_connection = mysql.connector.connect(
            host=host,
            user='root',
            password='MyNewPass',
            database='NHKdb',
            port=3306
        )
        print("✅ Successfully connected to MySQL.")
    except Exception as e:
        print("❌ Could not connect to MySQL:", e)

    return sql_connection

def get_last_processed_id():
    try:
        with get_sql_connection() as sql_connection:
            with sql_connection.cursor() as cursor:
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
                    return None  # Explicit None if no data

    except mysql.connector.Error as err:
        print(f"Database error while getting last processed ID: {err}")
        return None

def update_last_processed_id(new_id):
    try:
        with get_sql_connection() as sql_connection:
            with sql_connection.cursor() as cursor:
                query = """
                INSERT INTO metadata (last_processed_id) 
                VALUES (%s)
                ON DUPLICATE KEY UPDATE last_processed_id = %s;
                """
                cursor.execute(query, (new_id, new_id))
                sql_connection.commit()

    except mysql.connector.Error as err:
        print(f"Database error while updating: {err}")

def read_mongo():
    try:
        mongo_client = get_mongo_client()
    except PyMongoError as e:
        print(f"❌ Mongo connection failed: {e}")

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
    # get MongoDB connection
    try:
        mongo_client = get_mongo_client()
    except PyMongoError as e:
        print(f"❌ Mongo connection failed: {e}")

    db = mongo_client['NHK_articles']
    article_collection = db['NHK_articles']

    last_processed_id = get_last_processed_id()
    batch_size = 1000
    total_processed = 0

    try:
        with get_sql_connection() as sql_connection:
            with sql_connection.cursor() as cursor:
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
        print(f"🎉 Done! Total documents processed: {total_processed}")

if __name__ == "__main__":
    batch_process()
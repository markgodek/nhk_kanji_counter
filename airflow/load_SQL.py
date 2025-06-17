import os, re, hashlib, mysql.connector

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
    print("🔎 Fetching last processed ID from metadata...")
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
                    print(f"✅ Last processed ID: {result[0]}")
                    return result[0]
                else:
                    print("⚠️ No processed ID found in metadata.")
                    return None
    except mysql.connector.Error as err:
        print(f"❌ Database error while getting last processed ID: {err}")
        return None

def update_last_processed_id(cursor, new_id):
    print(f"📝 Updating last processed ID to: {new_id}")
    try:
        cursor.execute("DELETE FROM metadata")
        cursor.execute("INSERT INTO metadata (last_processed_id) VALUES (%s)", (new_id,))
    except mysql.connector.Error as err:
        print(f"❌ Database error while updating: {err}")

def count_kanji(document):
    return dict(Counter(re.findall(r'[\u4e00-\u9faf]', document['text'])))

def batch_process():
    try:
        mongo_client = get_mongo_client()
    except PyMongoError as e:
        print(f"❌ Mongo connection failed: {e}")
        return

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

                    cursor.execute("SELECT text_hash FROM processed_hashes")
                    known_hashes = set(row[0] for row in cursor.fetchall())

                    batch_kanji_counter = Counter()
                    new_hashes = []

                    for document in batch:
                        text_hash = document['text_hash']
                        if text_hash in known_hashes:
                            continue

                        kanji_counts = count_kanji(document)
                        batch_kanji_counter.update(kanji_counts)
                        new_hashes.append((text_hash,))
                        known_hashes.add(text_hash)
                        total_processed += 1

                    if batch_kanji_counter:
                        query = """
                        INSERT INTO kanji_count (kanji, count)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE count = count + VALUES(count);
                        """
                        params = [(k, c) for k, c in batch_kanji_counter.items()]
                        cursor.executemany(query, params)

                    if new_hashes:
                        cursor.executemany("INSERT IGNORE INTO processed_hashes (text_hash) VALUES (%s)", new_hashes)

                    # Always advance to the last ID in the batch
                    last_processed_id = str(batch[-1]['_id'])
                    update_last_processed_id(cursor, last_processed_id)
                    sql_connection.commit()

                    print(f"✅ Processed {total_processed} documents. Last ID: {last_processed_id}")

    except Exception as e:
        print(f"❌ Error during batch processing: {e}")

    finally:
        print(f"🎉 Done! Total documents processed: {total_processed}")



if __name__ == "__main__":
    batch_process()

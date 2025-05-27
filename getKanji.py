import os
from pymongo import MongoClient
from bson.objectid import ObjectId


def get_kanji():
    # Connect to the MongoDB dynamically in container vs debugging locally in PyCharm
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    client = MongoClient(f'mongodb://{mongo_host}:27017')

    # Fetch last processed _id from SQL or a state store
    last_processed_id = get_last_processed_id()  # e.g., from SQL or file

    query = {"_id": {"$gt": ObjectId(last_processed_id)}} if last_processed_id else {}
    batch_size = 1000

    while True:
        batch = list(
            collection.find(query).sort("_id", 1).limit(batch_size)
        )
        if not batch:
            break

        for doc in batch:
            processed = process(doc)
            save_to_sql(processed)
            last_processed_id = str(doc["_id"])

        # Save progress after each batch
        update_last_processed_id(last_processed_id)

    # extract only the kanji
    for article in articles:
        text = article.text
        kanji = re.findall(r'[\u4e00-\u9faf]+', text)
        print(text)
        print(kanji)



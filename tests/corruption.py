from pathlib import Path
from threading import Thread
import orjson
from tinydb import Query, TinyDB
from BetterJSONStorage import BetterJSONStorage
Thread
p = Path('pytest/empty.db')

with open("tests/json/citm_catalog.json", "rb") as f:
    data = orjson.loads(f.read())
transforms = {
    "events": [item for item in data["events"].values()],
    "seatCategoryNames": [
        {
            "category": name,
            "ids": [
                id
                for id in data["seatCategoryNames"]
                if data["seatCategoryNames"][id] == name
            ],
        }
        for name in (v for v in data["seatCategoryNames"].values())
    ],
    "areaNames": [{"id": k, "name": v} for k, v in data["areaNames"].items()],
    "audienceSubCategoryNames": [
        {"id": k, "name": v} for k, v in data["audienceSubCategoryNames"].items()
    ],
    "subTopicNames": [{"id": k, "name": v} for k, v in data["subTopicNames"].items()],
    "topicNames": [{"id": k, "name": v} for k, v in data["topicNames"].items()],
    "performances": data["performances"],
}

# group topics and subtopics together, no need to be in seperate tables
topics = []
for topic in transforms["topicNames"]:
    topics.append(
        {
            "id": topic["id"],
            "name": topic["name"],
            "subtopic": [
                subtopic
                for subtopic in transforms["subTopicNames"]
                if int(subtopic["id"]) in data["topicSubTopics"][topic["id"]]
            ],
        }
    )

with TinyDB(p, access_mode='r+', storage=BetterJSONStorage) as db :
    db.drop_tables()
    for table in data:
        if table not in ("topicNames", "subTopicNames", "topicSubTopics"):
            db.table(table).insert_multiple(transforms[table])
            db.table(table).remove(doc_ids=[1])
            db.table(table).insert({})
            db.table(table).insert_multiple(transforms[table])
            db.table(table).remove(doc_ids=[2])
            db.table(table).insert({})
            db.table(table).insert({})
            db.table(table).insert({})
            db.table(table).insert({})
    print(db)


with TinyDB(p, access_mode='r', storage=BetterJSONStorage) as db :
    for table in data:
        print([x for x in db.table(table).all() if x == {}])
        print(db.table(table).get(doc_id=1))
        print(db.table(table).get(doc_id=2))
        print(db.table(table).get(doc_id=3))

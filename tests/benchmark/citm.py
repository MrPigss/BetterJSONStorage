from pathlib import Path
from time import perf_counter_ns

import orjson
from tinydb import Query, TinyDB

from BetterJSONStorage import BetterJSONStorage


def write(db: TinyDB):
    start_write = perf_counter_ns()
    db.drop_tables()
    for _ in range(15):
        for table in data:
            if table not in ("topicNames", "subTopicNames", "topicSubTopics"):
                db.table(table).insert_multiple(transforms[table])
        db.table("topics").insert_multiple(topics)
    print(f"\t{perf_counter_ns()-start_write}ns writing")


def read(db: TinyDB):
    start_read = perf_counter_ns()
    topic = Query()
    subtopic = Query()
    for _ in range(15):
        table = db.table("topics")
        for sub in (
            337184268,
            337184288,
            337184284,
            337184263,
            337184298,
            337184269,
            337184280,
            337184297,
            337184281,
            337184296,
            337184279,
        ):
            table.get(topic.subtopic.any(subtopic.id == sub))
    print(f"\t{perf_counter_ns()-start_read}ns reading")


# load citm.json
with open("benchmark/citm_catalog.json", "rb") as f:
    data = orjson.loads(f.read())

# transform the data so it fits the 'document store' model better (no data has been deleted, only transformed)
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

start = perf_counter_ns()
with TinyDB(
    Path("benchmark/db/test_citm.db"), access_mode="r+", storage=BetterJSONStorage
) as db:
    write(db)
    read(db)
end_threaded = perf_counter_ns() - start

start = perf_counter_ns()
with TinyDB("benchmark/db/test_citm2.db") as db:
    write(db)
    read(db)
end_default = perf_counter_ns() - start

print(
    f"Total: \n\tBetterJsonStorage: {end_threaded/1000000}ms\n\tdefault jsonStorage: {end_default/1000000}ms\ndifference: \n\tbjs: {end_threaded/end_threaded:.2}x\n\tdjs: {end_default/end_threaded:.3}x"
)

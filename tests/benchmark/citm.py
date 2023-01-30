from pathlib import Path
from time import perf_counter_ns
import orjson
from tinydb import Query, TinyDB

from BetterJSONStorage import BetterJSONStorage

# load citm.json
with open("tests/data/citm_catalog.json", "rb") as f:
    data = orjson.loads(f.read())

# transform the data so it fits the 'document store' model better (same data - different format).
# this makes them easier to query, reason about, store, ...
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
topics = [
    {
        "id": topic["id"],
        "name": topic["name"],
        "subtopic": [
            subtopic for subtopic in transforms["subTopicNames"]
            if int(subtopic["id"]) in data["topicSubTopics"][topic["id"]]
        ],
    } for topic in transforms["topicNames"]
]


def write(db: TinyDB):
    start_w = perf_counter_ns()
    # start from clean empty table
    db.drop_tables()

    # do it multiple times just to be shure
    for _ in range(15):

        # loop over root nodes of the citm_catalog.json
        # these should be:
        # areaNames, audienceSubCategoryNames, events, performances, 
        # seatCategoryNames, subTopicNames, topicNames, topicSubTopics
        for table in data:

            # ignore these nodes -> these will be added seperatly
            if table not in ("topicNames", "subTopicNames", "topicSubTopics"):

                # add the transformed data to the table
                db.table(table).insert_multiple(transforms[table])

        # now add all the topics and subtopics
        db.table("topics").insert_multiple(topics)
    print(f"\twriting took: {(perf_counter_ns()-start_w)/1_000_000}ms")


def read(db: TinyDB):
    start_r = perf_counter_ns()
    topic = Query()
    subtopic = Query()
    for _ in range(15):

        # select the topics table
        table = db.table("topics")
        # loop over the subtopic id's 
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
            # return the document with the matching id
            table.get(topic.subtopic.any(subtopic.id == sub))
    print(f"\treading took: {(perf_counter_ns()-start_r)/1_000_000}ms")

# #################### #
#   Actual benchmark   #  
# #################### # 
start = perf_counter_ns()
with TinyDB(Path("benchmark/db/test_citm.db"), access_mode="r+", storage=BetterJSONStorage) as db:
    print("BetterJSONStorage:")
    write(db)
    read(db)
end_betterjson = perf_counter_ns() - start

start = perf_counter_ns()
with TinyDB("tests/benchmark/db/test_citm2.db") as db:
    print("Default JSONStorage:")
    write(db)
    read(db)
end_default = perf_counter_ns() - start

# print out the time it took + the time compared to BetterJSONStorage
print(
f"""
Total: 
    BetterJsonStorage: {end_betterjson / 1_000_000}ms
    default jsonStorage: {end_default / 1_000_000}ms

relative time vs BetterJSONStorage: 
    BetterJSONStorage: 1x
    JSONStorage: {end_default / end_betterjson:.5}x
"""
)

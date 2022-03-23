import cProfile
from pathlib import Path

from orjson import loads
from tinydb import Query, TinyDB

from BetterJSONStorage import BetterJSONStorage


# benchmark for writing
def write(db: TinyDB):
    db.drop_tables()
    for table in data:
        if table not in ("topicNames", "subTopicNames", "topicSubTopics"):
            db.table(table).insert_multiple(transforms[table])
    db.table("topics").insert_multiple(topics)


# benchmark for reading
def read(db: TinyDB):
    topic = Query()
    subtopic = Query()
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


# load citm.json
with open("tests/data/citm_catalog.json", "rb") as f:
    data = loads(f.read())

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


def better():
    with TinyDB(
        Path("tests/benchmark/db/test_citm.db"), access_mode="r+", storage=BetterJSONStorage
    ) as db:
        db.insert({"a": "b"})
    pass


def default():
    with TinyDB("tests/benchmark/db/test_citm2.db") as db:
        db.insert({"a": "b"})
    pass


with TinyDB(
    Path("tests/benchmark/db/test_citm.db"), access_mode="r+", storage=BetterJSONStorage
) as db:
    cProfile.run("write(db)", "tests/benchmark/prof/better_write.prof")
    cProfile.run("read(db)", "tests/benchmark/prof/better_read.prof")

with TinyDB("tests/benchmark/db/test_citm2.db") as db:
    cProfile.run("write(db)", "tests/benchmark/prof/default_write.prof")
    cProfile.run("read(db)", "tests/benchmark/prof/default_read.prof")

cProfile.run("default()", "tests/benchmark/prof/default_init.prof")
cProfile.run("better()", "tests/benchmark/prof/better_init.prof")


import os

for test in {"init", "read", "write"}:
    for x in {"default", "better"}:
        os.system(
            f"gprof2dot -n0 -e0 -f pstats tests/benchmark/prof/{x}_{test}.prof | dot -Tpng -o tests/benchmark/callgraphs/{x}_{test}.png"
        )

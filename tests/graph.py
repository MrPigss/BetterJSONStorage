import os
from pathlib import Path
from orjson import loads
from tinydb import TinyDB
from BetterJSONStorage import BetterJSONStorage
from time import perf_counter_ns as perf, sleep

with open("tests/random_100kb.json", "rb") as f:
    data = loads(f.read())


def read(db: TinyDB):
    # for i in range(0,139):
    #     db.get(doc_id=i)
    db.insert_multiple(data)
    print(db.get(doc_id=1))


def write(db):
    for item in data:
        db.insert(item)


scores: dict[str, dict[str, list]] = {
    "writes": {"BetterJSONStorage": [], "default_inserts": []}
}
db_file = Path("tests/random_100k.db")

if db_file.exists():
    os.remove(db_file)

for _ in range(10):
    with TinyDB(
        Path("tests/random_100k.db"), access_mode="r+", storage=BetterJSONStorage
    ) as db:
        start = perf()
        # write(db)
        read(db)
        scores["writes"]["BetterJSONStorage"].append(perf() - start)

    sleep(0.1)
    if db_file.exists():
        os.remove(db_file)

for _ in range(10):
    with TinyDB("tests/random_100k.db", encoding="utf8") as db:
        start = perf()
        # write(db)
        read(db)
        scores["writes"]["default_inserts"].append(perf() - start)
    sleep(0.1)
    if db_file.exists():
        os.remove(db_file)

# for test in scores['writes']:
#     for score in scores['writes'][test]:
#         print(score)

import os
from pathlib import Path
from orjson import loads
from tinydb import TinyDB
from BetterJSONStorage import BetterJSONStorage
from time import perf_counter_ns as perf, sleep
from tempfile import TemporaryFile

json_file = Path("tests/data/random_100kb.json")
db_file = Path("tests/data/random_100k.db")

scores: dict[str, dict[str, list]] = {
    "writes": {"BetterJSONStorage": [], "default_inserts": []}
}

with open(json_file, "rb") as f:
    data = loads(f.read())

def read(db: TinyDB):
    db.insert_multiple(data)
    db.get(doc_id=1)

def write(db: TinyDB):
    for item in data:
        db.insert(item)


if db_file.exists():
    os.remove(db_file)

for _ in range(10):
    with TinyDB(
        Path(db_file), access_mode="r+", storage=BetterJSONStorage
    ) as db:
        start = perf()
        # write(db)
        read(db)
        scores["writes"]["BetterJSONStorage"].append(perf() - start)

    sleep(0.1)
    if db_file.exists():
        os.remove(db_file)

for _ in range(10):
    with TinyDB(db_file, encoding="utf8") as db:
        start = perf()
        # write(db)
        read(db)
        scores["writes"]["default_inserts"].append(perf() - start)
    sleep(0.1)
    if db_file.exists():
        os.remove(db_file)

for test in scores['writes']:
    for score in scores['writes'][test]:
        print(score)

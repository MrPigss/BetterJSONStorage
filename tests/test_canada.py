from betterJSONStorage import BetterJSONStorage
from tinydb import TinyDB, Query
import orjson
from time import perf_counter

with open('tests/json/canada.json', 'rb') as f:
    data = orjson.loads(f.read())

start = perf_counter()
with TinyDB('tests/db/test_canada.db', storage=BetterJSONStorage) as db:
    q = Query()
    db.get(q.features.type == "Feature")
    # db.drop_tables()
    # db.insert(data)
end_better = perf_counter()-start

start = perf_counter()
with TinyDB('tests/db/test_canada2.db') as db:
    q = Query()
    db.get(q.features.type == "Feature")
    # db.drop_tables()
    # db.insert(data)
end_default = perf_counter()-start

print(f"BetterJsonStorage: {end_better}ms\ndefault jsonStorage: {end_default}ms\ndifference: {round(end_default/end_better, 2)}x")
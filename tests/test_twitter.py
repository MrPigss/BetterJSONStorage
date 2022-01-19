from betterJSONStorage import BetterJSONStorage
from tinydb import Query, TinyDB
from time import perf_counter
import orjson

with open('tests/json/twitter.json', 'rb') as f:
    data = orjson.loads(f.read())

start = perf_counter()
with TinyDB('tests/db/test_twitter.db', storage=BetterJSONStorage) as db:
    # q = Query()
    # db.get(q.id == 505874873759977500)
    db.drop_tables()
    db.insert_multiple(data['statuses'])
end_better = perf_counter()-start

start = perf_counter()
with TinyDB('tests/db/test_twitter2.db') as db:
    # q = Query()
    # db.get(q.id == 505874873759977500)
    db.drop_tables()
    db.insert_multiple(data['statuses'])
end_default = perf_counter()-start

print(f"BetterJsonStorage: {end_better}ms\ndefault jsonStorage: {end_default}ms\ndifference: {round(end_default/end_better, 2)}x")
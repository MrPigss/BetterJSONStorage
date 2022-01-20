from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB, Query
import orjson
from time import perf_counter

with open('tests/json/citm_catalog.json', 'rb') as f:
    data = orjson.loads(f.read())

start = perf_counter()
with TinyDB('tests/db/test_citm.db', storage=BetterJSONStorage) as db:
    q = Query()
    db.table('events').get(q.id == 138586965)
    # db.drop_tables()
    # for key in data:
    #     if isinstance(data[key], Dict):
    #         if key == 'events':
    #             x = [item for item in data[key].values()]
    #         else:
    #             x = [{k:v} for k,v in data[key].items()]
    #         db.table(key).insert_multiple(x)

    #     if isinstance(data[key], List):
    #         db.table(key).insert_multiple(data[key])
end_better = perf_counter()-start

start = perf_counter()
with TinyDB('tests/db/test_citm2.db') as db:
    q = Query()
    db.table('events').get(q.id == 138586965)
    # db.drop_tables()
    # for key in data:
    #     if isinstance(data[key], Dict):
    #         if key == 'events':
    #             x = [item for item in data[key].values()]
    #         else:
    #             x = [{k:v} for k,v in data[key].items()]
    #         db.table(key).insert_multiple(x)

    #     if isinstance(data[key], List):
    #         db.table(key).insert_multiple(data[key])
end_default = perf_counter()-start

print(f"BetterJsonStorage: {end_better}ms\ndefault jsonStorage: {end_default}ms\ndifference: {round(end_default/end_better, 2)}x")




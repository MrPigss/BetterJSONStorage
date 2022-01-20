from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB, Query

with TinyDB('tests/db/test_citm.db', storage=BetterJSONStorage) as db:
    q = Query()
    print(db.table('seatCategoryNames').all())
    x = {}
    print(x['henk'])

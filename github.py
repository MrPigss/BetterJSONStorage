from pathlib import Path
import orjson
from tinydb import Query, TinyDB
from BetterJSONStorage import BetterJSONStorage

p =Path("benchmark/db/test_citm.db")
with TinyDB(p, access_mode="r+", storage=BetterJSONStorage) as db:
    areanames = db.table('areaNames')
    q = Query()
    item_filter = (q.id.matches(r'^205705.*')) & (q.name.matches(r'^2.*'))# the query you want to use in search
    id_filter = lambda item: 2 < item.doc_id# the check for the correct id's

    result = [item for item in areanames.search(item_filter) if id_filter(item)]

print(result)
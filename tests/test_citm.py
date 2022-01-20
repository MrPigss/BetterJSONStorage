from tinydb.database import TableBase
from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB, Query
import orjson
from time import perf_counter

def write(db):
    start_write = perf_counter()
    db.drop_tables()
    for table in data:
        if table not in ('topicNames', 'subTopicNames', 'topicSubTopics'):
            db.table(table).insert_multiple(transforms[table])
    db.table('topics').insert_multiple(topics)
    print(f'\t{perf_counter()-start_write:e}ms writing')

def read(db: TinyDB):
    start_read = perf_counter()
    topic = Query()
    subtopic = Query()
    table = db.table('topics')
    x = table.get(topic.subtopic.any(subtopic.id == '337184267'))
    print(f'\t{perf_counter()-start_read:e}ms reading')


# load citm.json
with open('tests/json/citm_catalog.json', 'rb') as f:
    data = orjson.loads(f.read())
# transform the data so it fits the 'document store' model better (no data has been deleted, only transformed)
transforms = {
    'events': [item for item in data['events'].values()],
    'seatCategoryNames':[{'category': name, 'ids':[id for id in data['seatCategoryNames'] if data['seatCategoryNames'][id] == name]} for name in (v for v in data['seatCategoryNames'].values())],
    'areaNames':[{'id':k, 'name':v} for k,v in data['areaNames'].items()],
    'audienceSubCategoryNames': [{'id':k, 'name':v} for k,v in data['audienceSubCategoryNames'].items()],
    'subTopicNames': [{'id':k, 'name':v} for k,v in data['subTopicNames'].items()],
    'topicNames': [{'id':k, 'name':v} for k,v in data['topicNames'].items()],
    'performances': data['performances']
}

# group topics and subtopics together, no need to be in seperate tables
topics = []
for topic in transforms['topicNames']:
    topics.append({
        'id':topic['id'],
        'name':topic['name'],
        'subtopic':[subtopic for subtopic in transforms['subTopicNames'] if int(subtopic['id']) in data['topicSubTopics'][topic['id']]]
    })




# test with BetterJSONStorage
print('BetterJSONStorage:')
start = perf_counter()
with TinyDB('tests/db/test_citm.db', storage=BetterJSONStorage) as db:
    write(db)
    read(db)
end_better = perf_counter()-start


# test with default JSONStorage
print('default JSONStorage:')
start = perf_counter()
with TinyDB('tests/db/test_citm2.db') as db:
    write(db)
    read(db)
end_default = perf_counter()-start


print(f"Total:\n\tBetterJsonStorage: {end_better:e}ms\n\tdefault jsonStorage: {end_default:e}ms\n\tdifference: {end_default/end_better:.3}x")




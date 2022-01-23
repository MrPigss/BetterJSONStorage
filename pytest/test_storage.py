import os
from pydoc import doc
import tempfile
from pathlib import Path
from time import sleep
from typing import Dict

import orjson
from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB
from tinydb.table import Document

import pytest

@pytest.fixture
def data():
    # load citm.json
    with open("citm_catalog.json", "rb") as f:
        data: Dict = orjson.loads(f.read())

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
        "subTopicNames": [
            {"id": k, "name": v} for k, v in data["subTopicNames"].items()
        ],
        "topicNames": [{"id": k, "name": v} for k, v in data["topicNames"].items()],
        "performances": data["performances"],
    }

    # group topics and subtopics together, no need to be in seperate tables
    result = {"topics": []}
    topics = []
    for topic in transforms["topicNames"]:
        result["topics"].append(
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
    for table in data:
        if table not in ("topicNames", "subTopicNames", "topicSubTopics"):
            result[table] = transforms[table]

    return result


@pytest.fixture
def db_path() -> None:
    return Path(tempfile.gettempdir())


@pytest.fixture
def db_file() -> None:
    p = Path(tempfile.gettempdir() + "\\db.db")
    yield Path(tempfile.gettempdir() + "\\db.db")
    if p.exists(): os.remove(p)


#
#
# Tests
#
#

class Test_path:
    def test_nonexisting_file_readonly(self, db_file):
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(db_file)

    def test_nonexisting_file_writing(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+").close()
        assert db_file.exists()

    def test_pre_existing_file_readonly(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+").close()
        assert db_file.exists()
        BetterJSONStorage(db_file).close()
        assert db_file.exists()

    def test_pre_existing_file_writing(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+").close()
        BetterJSONStorage(db_file, access_mode="r+").close()
        assert db_file.exists()



class Test_reads:
    def test_reading_empty_file(self):
        with TinyDB("empty.db", storage=BetterJSONStorage) as db:
            assert db.get(123) == None
            assert db.contains(doc_id=123) == False
            assert db.tables() == set()
            assert db.all() == []

    def test_reading(self):
        with TinyDB("test_citm.db", storage=BetterJSONStorage) as db:
            table = db.table("topics")
            assert isinstance(table.get(doc_id=1), Document)

class Test_writes:
    def test_writing_to_readonly(self):
        with pytest.raises(PermissionError):
            with TinyDB("empty.db", storage=BetterJSONStorage) as db:
                db.insert({})

    def test_writing(self):
        with TinyDB("empty.db", access_mode='r+', storage=BetterJSONStorage) as db:
            insert = db.insert({})
            assert db.get(doc_id=insert) == {}
            db.remove(doc_ids=[insert])
            sleep(.1)
            assert db.get(doc_id=insert) == None
            Path("empty.db").write_bytes(b'') #Todo Fix this

    def test_writing_different_instances(self, db_file):
        test_dict = {"Test": u"こんにちは世界"}

        storage_one = BetterJSONStorage(db_file, access_mode='r+')
        storage_two = BetterJSONStorage(db_file)

        storage_one.write(test_dict)
        sleep(0.1)

        assert storage_one.read() == test_dict
        assert storage_two.read() == None
        storage_two.load()
        assert storage_two.read() == test_dict


        assert storage_one.read() == storage_two.read()

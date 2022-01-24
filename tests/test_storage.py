import os
import tempfile
from pathlib import Path
from time import sleep
from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB

import pytest

@pytest.fixture
def db_file() -> None:
    p = Path(tempfile.gettempdir() + "\\db.db")
    yield p
    if p.exists():
        os.remove(p)


@pytest.fixture
def empty_db_file() -> None:
    p = Path(tempfile.gettempdir() + "\\empty.db")
    p.touch()
    Path("empty.db").write_bytes(b"")
    yield p
    if p.exists():
        os.remove(p)


#
# Tests
#
#

class Test_basic_functionality():
    # assume a file exists, content doesn't matter
    def test_load_file(self, empty_db_file):
        BetterJSONStorage(empty_db_file)

    # path is given, file doesn't exist.
    def test_write_file_noPerm(self, db_file):
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(db_file)

    # path is given, file doesn't exist permission to write.
    def test_write_file(self, db_file):
        BetterJSONStorage(db_file, access_mode="r+")
        assert db_file.exists()

class Test_path:
    def test_path_is_directory_readonly(self):
        p = Path()  # returns the current working dir
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(p)

    def test_default_path(self):
        with pytest.raises(TypeError):
            BetterJSONStorage()

    def test_nonexisting_file_readonly(self, db_file):
        assert db_file.exists() == False
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(db_file)

    def test_nonexisting_file_writing(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+")
        assert db_file.exists()

    def test_pre_existing_file_readonly(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+")
        assert db_file.exists()
        BetterJSONStorage(db_file)
        assert db_file.exists()

    def test_pre_existing_file_writing(self, db_file):
        assert not db_file.exists()
        BetterJSONStorage(db_file, access_mode="r+")
        BetterJSONStorage(db_file, access_mode="r+")
        assert db_file.exists()

class Test_access_modes:
    # file exists permissions differ
    def test_acces_mode(self, empty_db_file):
        BetterJSONStorage(empty_db_file, access_mode="r")
        BetterJSONStorage(empty_db_file, access_mode="r+")
        with pytest.raises(AttributeError):
            BetterJSONStorage(empty_db_file, access_mode="+")
            BetterJSONStorage(empty_db_file, access_mode="")
            BetterJSONStorage(empty_db_file, access_mode="x")

class Test_multiple_instances:
    def test_different_paths(self, db_file):
        p = Path(str(db_file) + "test.db")
        x = BetterJSONStorage(db_file, access_mode="r+")
        y = BetterJSONStorage(p, access_mode="r+")

        os.remove(p)

    # def test_same_paths(self, db_file):
    #     pass


class Test_reads:
    def test_reading_empty_file(self, empty_db_file):
        db = TinyDB(empty_db_file, Storage=BetterJSONStorage)
        assert db.get(123) == None
        assert db.contains(doc_id=123) == False
        assert db.tables() == set()
        assert db.all() == []
        db.close()

    def test_reading(self):
        doc = {
            "id": "107888604",
            "name": "Activité",
            "subtopic": [
                {"id": "337184267", "name": "Ciné-concert"},
                {"id": "337184283", "name": "Concert"},
            ],
        }
        p = Path("tests/test_citm.db")
        with TinyDB(p, storage=BetterJSONStorage) as db:
            assert db.table("topics").get(doc_id=1) == doc


class Test_writes:
    def test_writing_to_readonly(self, db_file):
        db_file.touch()
        with pytest.raises(PermissionError):
            with TinyDB(db_file, storage=BetterJSONStorage) as db:
                db.insert({})

    def test_writing(self, db_file):
        with TinyDB(db_file, access_mode="r+", storage=BetterJSONStorage) as db:
            insert = db.insert({})
            assert db.get(doc_id=insert) == {}
            db.remove(doc_ids=[insert])
            assert db.get(doc_id=insert) == None
            sleep(0.1)


    def test_writing_different_instances(self, db_file):
        with pytest.raises(AttributeError):
            x = BetterJSONStorage(db_file, access_mode="r+")
            y = BetterJSONStorage(db_file)

    def test_continuety_between_instances(self, db_file):
        test_dict = {"Test": "test"}
        with TinyDB(db_file, access_mode="r+", storage=BetterJSONStorage) as db:
            x = db.insert(test_dict)

        sleep(0.1)
        with TinyDB(db_file, access_mode="r+", storage=BetterJSONStorage) as db:
            assert db.get(doc_id=x) == test_dict

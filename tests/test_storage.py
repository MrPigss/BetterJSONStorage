import os
import tempfile
from pathlib import Path
from time import sleep
from BetterJSONStorage import BetterJSONStorage
from tinydb import TinyDB

import pytest

@pytest.fixture
def db_file():
    p = Path(tempfile.gettempdir() + "\\db.db")
    yield p
    if p.exists():
        os.remove(p)


@pytest.fixture
def empty_db_file():
    p = Path(tempfile.gettempdir() + "\\empty.db")
    p.touch()
    p.write_bytes(b"")
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
        BetterJSONStorage(empty_db_file).close()

    # path is given, file doesn't exist.
    def test_write_file_noPerm(self, db_file):
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(db_file).close()

    # path is given, file doesn't exist permission to write.
    def test_write_file(self, db_file):
        BetterJSONStorage(db_file, access_mode="r+").close()
        assert db_file.exists()

class Test_path:
    def test_path_is_not_of_type_Path(self):
        p = './data/test_citm.db'
        with pytest.raises(TypeError):
            BetterJSONStorage(p).close()

    def test_path_is_directory_readonly(self):
        p = Path()  # returns the current working dir
        with pytest.raises(FileNotFoundError):
            BetterJSONStorage(p).close()

    def test_default_path(self):
        with pytest.raises(TypeError):
            BetterJSONStorage().close()

    def test_nonexisting_file_readonly(self, db_file):
        assert db_file.exists() == False
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

class Test_access_modes:
    # file exists permissions differ
    def test_acces_mode(self, empty_db_file):
        BetterJSONStorage(empty_db_file, access_mode="r").close()
        BetterJSONStorage(empty_db_file, access_mode="r+").close()
        with pytest.raises(AttributeError):
            BetterJSONStorage(empty_db_file, access_mode="+").close()
            BetterJSONStorage(empty_db_file, access_mode="").close()
            BetterJSONStorage(empty_db_file, access_mode="x").close()

class Test_multiple_instances:
    def test_different_paths(self, db_file):
        p = Path(f"{str(db_file)}test.db")
        x = BetterJSONStorage(db_file, access_mode="r+").close()
        y = BetterJSONStorage(p, access_mode="r+").close()

        os.remove(p)

    # def test_same_paths(self, db_file):
    #     pass


class Test_reads:
    def test_reading_empty_file(self, empty_db_file):
        db = TinyDB(empty_db_file, Storage=BetterJSONStorage)
        assert db.get(123) is None
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
        p = Path("tests/data/test_citm.db")
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
            assert db.get(doc_id=insert) is None
            sleep(0.1)


    def test_writing_different_instances(self, db_file):
        with pytest.raises(AttributeError):
            x = BetterJSONStorage(db_file, access_mode="r+")
            y = BetterJSONStorage(db_file)

        x.close()

    def test_continuety_between_instances(self, db_file):
        test_dict = {"Test": "test"}
        with TinyDB(db_file, access_mode="r+", storage=BetterJSONStorage) as db:
            x = db.insert(test_dict)

        with TinyDB(db_file, storage=BetterJSONStorage) as db:
            assert db.get(doc_id=x) == test_dict


    def test_repr(self, db_file):
         with TinyDB(db_file, access_mode="r+", storage=BetterJSONStorage) as db:
           print(db.storage)

from io import BytesIO
from threading import Thread
from orjson import loads, dumps
from blosc import compress, decompress
from tinydb import Storage
import os

def touch(path: str, create_dirs):
    base_dir = os.path.dirname(path)
    if create_dirs:
        base_dir = os.path.dirname(path)
        if not os.path.exists(base_dir): os.makedirs(base_dir)
    with open(path, 'a'): ...

class BetterJSONStorage(Storage):

    def __init__(self, path: str, access_mode='r+', create_dirs=False,**kwargs):
        super().__init__()
        self._kwargs = kwargs

        if any([character in access_mode for character in ('+', 'w', 'a')]):
            touch(path, create_dirs)
        self._handle = open(path, mode=access_mode+'b')

    def close(self):
        self._handle.close()

    def read(self):
        self._handle.seek(0, os.SEEK_END)
        if not self._handle.tell(): return None
        self._handle.seek(0)
        return loads(decompress(self._handle.read()))

    def write(self, data):
        self._handle.seek(0)
        self._handle.write(compress(dumps(data, **self._kwargs)))
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.truncate()


class testStorage(Storage):

    class AsyncWriter(Thread):
        """
        Custom Thread class.

        When called, the thread:
        1.  opens the file from disk
        2.  parses the data to json
        3.  compresses the json
        4.  writes compressed json to disk
        5.  exists.

        """
        def __init__(self, filename, data):
            Thread.__init__(self, daemon=True)
            self.filename = filename
            self.data = data

        def run(self):
            with open(self.filename, 'wb') as f:
                f.write(compress(dumps(self.data)))

    def __init__(self, path: str, access_mode='r+', create_dirs=False,**kwargs):
        self._kwargs = kwargs
        self._path = path

        if any([character in access_mode for character in ('+', 'w', 'a')]):
            touch(path, create_dirs)

        # only open and decompress the file from storage once.
        # then read and put the data in memory
        self.load()

    # really isn't necesarry
    def close(self):
        del self._handle

    # just read from memory, no need to open the file.
    def read(self):
        return self._handle


    def write(self, data):
        """
        Writes data to file.

        First data is saved in memory for faster acces.
        For parsing json, compressing, and writing the file to disk a new thread is spawned
        so the current thread is not blocked.
        """
        self._handle = data
        self.AsyncWriter(fileanem=self._path, data=self._handle).start()

    def load(self):
        """
        Sets the data in memory to the contents of the file.
        This is done on object creation.

        Can be done manually to ensure data is synchronised. (shouldn not be necesarry)
        """
        with open(self._path, mode='rb') as handle:
            # check if file is empty
            handle.seek(0,2)
            if not handle.tell(): return None
            # if not empty, read it
            handle.seek(0)
            self._handle = loads(decompress(handle.read()))


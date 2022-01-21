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
        def __init__(self, filename, data):
            Thread.__init__(self, daemon=True)
            self.filename = filename
            self.data = data

        def run(self):
            with open(self.filename, 'wb') as f:
                f.write(compress(self.data))

    def __init__(self, path: str, access_mode='r+', create_dirs=False,**kwargs):
        self._kwargs = kwargs
        self._path = path

        if any([character in access_mode for character in ('+', 'w', 'a')]):
            touch(path, create_dirs)

        # only open and decompress the file from storage once.
        # then read and put the data in memory
        with open(path, mode='rb') as handle:
            self._handle = BytesIO(decompress(handle.read()))

    # close the memory buffer
    def close(self):
        self._handle.close()

    # only read from memorybuffer
    def read(self):
        self._handle.seek(0,2) # go to the end of the file
        if not self._handle.tell(): return None # if tell returns zero file is empty
        return loads(self._handle.getvalue()) # read from the buffer


    def write(self, data):
        serialized = dumps(data, **self._kwargs) # serialize data from table
        self._handle.seek(0) #got to the start of the 'file'
        self._handle.write(serialized) # write the serialized file
        self._handle.truncate() # truncate in case the 'file' got smaller

        # since everything has been done in memory it's not on disk yet
        # compress and write to disk in a seperate daemon thread
        # so we don't block the current one
        self.AsyncWriter(self._path, serialized).start()


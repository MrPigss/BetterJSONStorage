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
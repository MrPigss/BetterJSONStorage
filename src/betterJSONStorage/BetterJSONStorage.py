import os
from pathlib import Path
from statistics import mode
from threading import Thread
from typing import Mapping

from blosc import compress, decompress
from orjson import dumps, loads
from tinydb import Storage


def touch(path: str, create_dirs):
    base_dir = os.path.dirname(path)
    if create_dirs:
        base_dir = os.path.dirname(path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    with open(path, "a"):
        ...


class BetterJSONStorage(Storage):
    def __init__(self, path: str, access_mode="r+", create_dirs=False, **kwargs):
        super().__init__()
        self._kwargs = kwargs

        if any([character in access_mode for character in ("+", "w", "a")]):
            touch(path, create_dirs)
        self._handle = open(path, mode=access_mode + "b")

    def close(self):
        self._handle.close()

    def read(self) -> Mapping:
        self._handle.seek(0, os.SEEK_END)
        if not self._handle.tell():
            return None
        self._handle.seek(0)
        return loads(decompress(self._handle.read()))

    def write(self, data):
        self._handle.seek(0)
        self._handle.write(compress(dumps(data, **self._kwargs)))
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.truncate()


class AsyncStorage(Storage):
    """
    A class that represents a storage interface for reading and writing to a file.


    Attributes
    ----------
    `path: str`
        Path to file, if it does not exist it will be created only if the the 'r+' access mode is set.

    `access_mode: str, optional`
        Options are `'r'` for readonly (default), or `'r+'` for writing and reading.

    `kwargs:`
        These attributes will be passed on to `orjson.dumps`

    Methods
    -------
    `read() -> Mapping:`
        Returns the data from memory.

    `write(data: Mapping) -> None:`
        Writes data to file if acces mode is set to `r+`.

    `load() -> None:`
        loads the data from disk. This happens on object creation.
        Can be used when you suspect the data in memory and on disk are not in sync anymore.

    Raises
    ------
    `FileNotFoundError` when the file doesn't exist and `r+` is not set

    Notes
    ----
    If the directory specified in `path` does not exist it will only be created if access_mode is set to `'r+'`.
    """

    class _AsyncWriter(Thread):
        def __init__(self, path: Path, data: Mapping):
            Thread.__init__(self)
            self.path = path
            self.data = data

        def run(self):
            self.path.write_bytes(compress(dumps(self.data)))

    def __init__(self, path: str, access_mode: str = "r", **kwargs):
        """
        Attributes
        ----------
        `path: str`
            Path to file, if it does not exist it will be created only if the the 'r+' access mode is set.

        `access_mode: str, optional`
            Options are `'r'` for readonly (default), or `'r+'` for writing and reading.

        `kwargs:`
            These attributes will be passed on to `orjson.dumps`

        Raises
        ------
        `FileNotFoundError` when the file doens't exist and `r+` is not set
        """
        self._kwargs = kwargs
        self._path = Path(path)
        self._acces_mode = access_mode

        if access_mode == "r+":
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch()

        self.load()

    def read(self) -> Mapping:
        return self._handle

    def write(self, data: Mapping) -> None:
        if not self._acces_mode == "r+":
            raise PermissionError("Storage is openend as read only")

        self._handle = data
        self._AsyncWriter(path=self._path, data=self._handle).start()

    def load(self) -> None:
        with open(self._path, mode="rb") as handle:
            # check if file is empty
            handle.seek(0, 2)
            if not handle.tell():
                return None
            # if not empty, read it
            handle.seek(0)
            self._handle = loads(decompress(handle.read()))

import _thread as Thread
from pathlib import Path
from typing import Mapping

from blosc import compress, decompress
from orjson import dumps, loads
from tinydb import Storage


class Singleton(object):
    _paths = []
    def __new__(class_, path, *args, **kwargs):
        h = hash(path)
        paths = class_._paths
        if h in paths:
            raise AttributeError(f'A BetterJSONStorage object already exists with path < "{path}" >')
        class_._paths.append(h)
        return object.__new__(class_)


class BetterJSONStorage(Storage, Singleton):
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
    def __del__(self):
        if (h := hash(self._path)) in (p := self.__class__._paths):
            p.remove(h)

    def __init__(self, path: Path = Path(), access_mode: str = "r", **kwargs):
        self._kwargs = kwargs
        self._path = path
        self._acces_mode = access_mode
        self._write_lock = Thread.allocate_lock()

        if not access_mode in ("r", "r+"):
            raise AttributeError(
                f'access_mode is not one of ("r", "r+"), :{access_mode}'
            )

        if access_mode == "r+":
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.touch()

        if path.is_file():
            self.load()
            return

        raise FileNotFoundError(
            f"""File can't be created because readOnly is set or path is an existing directory.
            Path: <{path.absolute()}>,
            Mode: <{"readOnly" if access_mode == "r" else "readWrite"}>,
            Is_directory: <{path.is_dir()}>
        """
        )

    def __repr__(self):
        return f"""BetterJSONStorage(path={self._path}, Paths={self.__class__._paths})"""

    def read(self) -> Mapping:
        return self._handle

    def _write_async(self):
        if self._handle:
            self._write_lock.acquire()
            with open(self._path, mode="wb") as f:
                f.write(compress(dumps(self._handle, **self._kwargs)))
            self._write_lock.release()

    def write(self, data: Mapping) -> None:
        if not self._acces_mode == "r+":
            raise PermissionError("Storage is openend as read only")

        self._handle = data
        Thread.start_new_thread(self._write_async, ())

    def load(self) -> None:
        if len(db_bytes := self._path.read_bytes()):
            self._handle = loads(decompress(db_bytes))
        else:
            self._handle = None

    def close(self):
        self.__class__._paths.remove(hash(self._path))

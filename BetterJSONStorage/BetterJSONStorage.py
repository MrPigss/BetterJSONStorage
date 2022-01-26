import _thread as Thread
from pathlib import Path
from typing import Mapping

from blosc import compress, decompress
from orjson import dumps, loads
from tinydb import Storage


class Access_mode:
    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __set__(self, obj, value):
        if not value in {"r", "r+"}:
            obj.close()
            raise AttributeError(f'access_mode is not one of ("r", "r+"), :{value}')
        setattr(obj, self.private_name, value)

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)


class FilePath:
    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __set__(self, obj, path):
        setattr(obj, self.private_name, path)
        if not isinstance(path, Path):
            obj.close()
            raise TypeError("path is not an instance of pathlib.Path")

        if not path.exists():
            if obj._access_mode == "r":
                obj.close()
                raise FileNotFoundError(
                    f"""File can't be found, use access_mode='r+' if you wan to create it.
                        Path: <{path.absolute()}>,
                        """
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        if not path.is_file():
            obj.close()
            raise FileNotFoundError(
                f"""path does not lead to a file: <{path.absolute()}>."""
            )

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)


class BetterJSONStorage(Storage):
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

    _paths = set()
    _access_mode = Access_mode()
    _path = FilePath()

    def __init__(self, path: Path = Path(), access_mode: str = "r", **kwargs):
        self._access_mode = access_mode
        self._path = path
        self._kwargs = kwargs
        self.load()

    def __new__(class_, path, *args, **kwargs):
        h = hash(path)
        if h in class_._paths:
            raise AttributeError(
                f'A BetterJSONStorage object already exists with path < "{path}" >'
            )
        class_._paths.add(h)
        instance = object.__new__(class_)
        setattr(instance, "_hash", h)
        return instance

    def __del__(self):
        self.close()

    def __repr__(self):
        return (
            f"""BetterJSONStorage(path={self._path}, Paths={self.__class__._paths})"""
        )

    def read(self) -> Mapping:
        return self._handle

    def _write_async(self):
        if self._handle:
            with open(self._path, mode="wb") as f:
                f.write(compress(dumps(self._handle, **self._kwargs)))

    def write(self, data: Mapping) -> None:
        if not self._access_mode == "r+":
            raise PermissionError("Storage is openend as read only")
        self._handle = data
        Thread.start_new_thread(self._write_async, ())

    def load(self) -> None:
        if len(db_bytes := self._path.read_bytes()):
            self._handle = loads(decompress(db_bytes))
        else:
            self._handle = None

    def close(self):
        if self._hash in (p := self.__class__._paths):
            p.remove(self._hash)

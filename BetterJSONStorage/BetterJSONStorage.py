import _thread as Thread
from pathlib import Path
from typing import Literal, Mapping, Optional, Set

from blosc import compress, decompress
from orjson import dumps, loads


class Access_mode:
    __slots__ = "name"

    def __set_name__(self, owner, name: str):
        self.name = f"{name}_"

    def __set__(self, obj, value: str):
        if not value in {"r", "r+"}:
            obj.close()
            raise AttributeError(f'access_mode is not one of ("r", "r+"), :{value}')
        setattr(obj, self.name, value)

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name)


class FilePath:
    __slots__ = "name"

    def __set_name__(self, _, name: str):
        self.name = f"{name}_"

    def __set__(self, obj, path: Path):
        setattr(obj, self.name, path)
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

    def __get__(self, obj, _=None):
        return getattr(obj, self.name)


class BetterJSONStorage:
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

    __slots__ = (
        "_hash",
        "_access_mode_",
        "_path_",
        "_handle",
        "_kwargs",
        "_changed",
        "_running",
        "_shutdown_lock",
    )

    _paths: Set[int] = set()
    _access_mode = Access_mode()
    _path = FilePath()

    def __init__(
        self, path: Path = Path(), access_mode: Literal["r", "r+"] = "r", **kwargs
    ):
        # flags
        self._shutdown_lock = Thread.allocate_lock()
        self._running = True
        self._changed = False

        # descriptors
        self._hash = hash(path)
        self._access_mode = access_mode
        self._path = path

        # rest
        self._kwargs = kwargs
        self._handle: Optional[Mapping]

        # finishing init
        self.load()
        Thread.start_new_thread(self.__file_writer, ())

    def __new__(class_, path, *args, **kwargs):
        h = hash(path)
        if h in class_._paths:
            raise AttributeError(
                f'A BetterJSONStorage object already exists with path < "{path}" >'
            )
        class_._paths.add(h)
        instance = object.__new__(class_)
        return instance

    def __repr__(self):
        return (
            f"""BetterJSONStorage(path={self._path}, Paths={self.__class__._paths})"""
        )

    def read(self):
        return self._handle

    def __file_writer(self):
        self._shutdown_lock.acquire()
        while self._running:

            if self._changed:
                self._changed = False
                self._path.write_bytes(compress(dumps(self._handle)))

        self._shutdown_lock.release()

    def write(self, data: Mapping):
        if not self._access_mode == "r+":
            raise PermissionError("Storage is openend as read only")
        self._handle = data
        self._changed = True

    def load(self) -> None:
        if len(db_bytes := self._path.read_bytes()):

            self._handle = loads(decompress(db_bytes))
        else:
            self._handle = None

    def close(self):
        while self._changed:
            ...
        self._running = False
        self._shutdown_lock.acquire()
        self.__class__._paths.discard(self._hash)

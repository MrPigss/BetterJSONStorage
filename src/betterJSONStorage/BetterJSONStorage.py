from pathlib import Path
from threading import Thread
from typing import Mapping, Union

from blosc import compress, decompress
from orjson import dumps, loads
from tinydb import Storage

# Todo Implement Locks
# Todo Make singelton
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

    class _AsyncWriter(Thread):
        def __init__(self, path: Path, data: Mapping, **kwargs):
            Thread.__init__(self)
            self.path = path
            self.data = data
            self.kwargs = kwargs

        def run(self):
            if self.data:
                self.path.write_bytes(compress(dumps(self.data, **self.kwargs)))

    def __init__(self, path: Union[str, Path], access_mode: str = "r", **kwargs):
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
        self._AsyncWriter(self._path, self._handle, **self._kwargs).start()

    def load(self) -> None:
        if len(db_bytes:=self._path.read_bytes()):
            self._handle = loads(decompress(db_bytes))
        else:
            self._handle = None

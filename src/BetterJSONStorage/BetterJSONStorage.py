# MIT License

# Copyright (c) 2022 Thomas Eeckhout

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import _thread as Thread
from io import BufferedRandom, BufferedWriter
from pathlib import Path
from typing import Literal, Mapping, Optional, Set, Union

from blosc2 import compress, decompress
from orjson import dumps, loads


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
        "_access_mode",
        "_path",
        "_data",
        "_kwargs",
        "_dump_kwargs",
        "_changed",
        "_running",
        "_shutdown_lock",
        "_handle",
    )

    _paths: Set[int] = set()

    def __init__(
        self, path: Path = Path(), access_mode: Literal["r", "r+"] = "r", **kwargs
    ):
        # flags
        self._shutdown_lock = Thread.allocate_lock()
        self._running = True
        self._changed = False

        # checks
        self._hash = hash(path)

        self._handle: Optional[Union[BufferedWriter, BufferedRandom]] = None
        if access_mode not in {"r", "r+"}:
            self.close()
            raise AttributeError(
                f'access_mode is not one of ("r", "r+"), :{access_mode}'
            )

        if not isinstance(path, Path):
            self.close()
            raise TypeError("path is not an instance of pathlib.Path")

        if not path.exists():
            if access_mode == "r":
                self.close()
                raise FileNotFoundError(
                    f"""File can't be found, use access_mode='r+' if you wan to create it.
                        Path: <{path.absolute()}>,
                        """
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = path.open("wb+")
        if not path.is_file():
            self.close()
            raise FileNotFoundError(
                f"""path does not lead to a file: <{path.absolute()}>."""
            )
        else:
            self._handle = path.open("rb+")

        self._access_mode = access_mode
        self._path = path

        # rest
        self._kwargs = kwargs
        self._dump_kwargs = {k: v for k, v in kwargs.items() if k in {'default', 'option'}}
        self._data: Optional[Mapping]

        # finishing init
        self.load()
        # only start the file write at all if the access mode is not read only
        if access_mode == "r+":
            Thread.start_new_thread(self.__file_writer, ())

    def __new__(cls, path, *args, **kwargs):
        h = hash(path)
        if h in cls._paths:
            raise AttributeError(
                f'A BetterJSONStorage object already exists with path < "{path}" >'
            )
        cls._paths.add(h)
        return object.__new__(cls)

    def __repr__(self):
        return (
            f"""BetterJSONStorage(path={self._path}, Paths={self.__class__._paths})"""
        )

    def read(self):
        return self._data

    def __file_writer(self):
        self._shutdown_lock.acquire()
        while self._running:

            if self._changed:
                self._changed = False
                self._handle.seek(0)
                self._handle.write(compress(dumps(self._data, **self._dump_kwargs)))

        self._shutdown_lock.release()

    def write(self, data: Mapping):
        if self._access_mode != "r+":
            raise PermissionError("Storage is openend as read only")
        self._data = data
        self._changed = True

    def load(self) -> None:
        if len(db_bytes := self._path.read_bytes()):

            self._data = loads(decompress(db_bytes))
        else:
            self._data = None

    def close(self):
        while self._changed:
            ...
        self._running = False
        self._shutdown_lock.acquire()
        if self._handle != None:
            self._handle.flush()
            self._handle.close()
        self.__class__._paths.discard(self._hash)

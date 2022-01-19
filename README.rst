.. image:: https://raw.githubusercontent.com/msiemens/tinydb/master/artwork/logo.png
    :scale: 100%
    :height: 150px

Introduction
************
BetterJSONStorage is a faster 'Storage Type' for TinyDB_.
It uses the faster Orjson_ library for parsing the JSON and BLOSC_ for compression.
Smaller filesizes result in faster reading and writing (less diskIO),
and the extra cost of (de-)compressing has been made up for by using the faster orjson.

An example of how to implement BetterJSONStorage can be found below.
Anything else can be found in the `TinyDB docs <https://tinydb.readthedocs.io/>`_.

Usage
************

context Manager
===============
.. code-block:: python

    >>> from tinydb import TinyDB
    >>> from BetterJSONStorage import BetterJSONStorage

    >>> with TinyDB('/path/to/db.json', storage=BetterJSONStorage) as db:
    >>>     db.insert({'int': 1, 'char': 'a'})
    >>>     db.insert({'int': 1, 'char': 'b'})

.. _TinyDB: https://github.com/msiemens/tinydb
.. _Orjson: https://github.com/ijl/orjson
.. _BLOSC: https://github.com/Blosc/python-blosc
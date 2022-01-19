.. image:: ./img/logo.png
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

    from tinydb import TinyDB
    from BetterJSONStorage import BetterJSONStorage

    with TinyDB('/path/to/file.db', storage=BetterJSONStorage) as db:
        db.insert({'int': 1, 'char': 'a'})
        db.insert({'int': 1, 'char': 'b'})

.. _TinyDB: https://github.com/msiemens/tinydb
.. _Orjson: https://github.com/ijl/orjson
.. _BLOSC: https://github.com/Blosc/python-blosc

extra
=====

All arguments except for the storage argument are forwarded to the underlying storage.
You can use this to pass additional keyword arguments to orjson.dumps(…) method.

For all options see the `orjson documentation <https://github.com/ijl/orjson#option>`_.

.. code-block:: python

    with TinyDB('file.db', option=orjson.OPT_NAIVE_UTC, storage=BetterJSONStorage) as db:

performance
************
The benchmarks are done on fixtures of real data:

* citm_catalog.json, 1.7MiB, concert data, containing nested dictionaries of strings and arrays of integers, indented.
* canada.json, 2.2MiB, coordinates of the Canadian border in GeoJSON format, containing floats and arrays, indented.
* twitter.json, 631.5KiB, results of a search on Twitter for "一", containing CJK strings, dictionaries of strings and arrays of dictionaries, indented.

data can be found `here <https://github.com/serde-rs/json-benchmark/tree/master/data>`_.

The exact same code is used for both BetterJSONStorage and the default JSONStorage.
BetterJSONStorage is faster in almost* all situations and uses significantly less space on disk.

citm_catalog.json
==================

.. list-table:: write_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.1182915
     - 1x
   * - default JSONStorage
     - 0.193683
     - 1.64x

.. list-table:: read_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.0098675
     - 1x
   * - default JSONStorage
     - 0.0099165
     - 1x

.. list-table:: storage used
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - used storage in kb
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 83.3
     - 1x
   * - default JSONStorage
     - 540
     - 6.48x

canada.json
==================

.. list-table:: write_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.0316401
     - 1x
   * - default JSONStorage
     - 0.0939051
     - 2.97x

.. list-table:: read_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.0276127
     - 1x
   * - default JSONStorage
     - 0.057871
     - 2.1x

.. list-table:: storage used
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - used storage in kb
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 1572
     - 1x
   * - default JSONStorage
     - 2150
     - 1.36x

twitter.json
==================

.. list-table:: write_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.0104866
     - 1x
   * - default JSONStorage
     - 0.0145437
     - 1.39x

.. list-table:: read_speed
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - time im ms
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 0.0069805
     - 1x
   * - default JSONStorage
     - 0.0078986
     - 1.13x

.. list-table:: storage used
   :widths: 25 25 25
   :header-rows: 1

   * - storage
     - used storage in kb
     - vs. BetterJSONStorage
   * - BetterJSONStorage
     - 155
     - 1x
   * - default JSONStorage
     - 574
     - 3.7x
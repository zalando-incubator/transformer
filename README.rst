
.. image:: docs/_static/transformer.png
   :alt: Transformer logo
   :align: center

|

.. image:: https://travis-ci.org/zalando-incubator/Transformer.svg?branch=master
   :alt: travis-ci status badge
   :target: https://travis-ci.org/zalando-incubator/Transformer

.. image:: https://badgen.net/pypi/v/har-transformer
   :alt: pypi version badge
   :target: https://pypi.org/project/har-transformer

.. image:: https://api.codacy.com/project/badge/Grade/10b3feb4e4814429bf288b87443a6c72
   :alt: code quality badge
   :target: https://www.codacy.com/app/thilp/Transformer

.. image:: https://api.codacy.com/project/badge/Coverage/10b3feb4e4814429bf288b87443a6c72
   :alt: test coverage badge
   :target: https://www.codacy.com/app/thilp/Transformer

.. image:: https://badgen.net/badge/code%20style/black/000
   :alt: Code style: Black
   :target: https://github.com/ambv/black


Transformer
***********

A **command-line tool** and **Python library** to convert web browser sessions
(`HAR`_ files) into Locust_ load test scenarios ("locustfiles").

.. _HAR: https://en.wikipedia.org/wiki/.har
.. _Locust: https://locust.io/

Use it to **replay HAR files** (storing recordings of interactions with your
website) **in load tests** with Locust_.

.. contents::
   :local:

Installation
============

Install from PyPI::

   pip install har-transformer

Usage
=====

Example HAR files are included in the ``examples/`` directory, try them
out.

Command-line
------------

.. code:: bash

   transformer my_har_files_directory/ >locustfile.py

Library
-------

.. code:: python

   import transformer

   with open("locustfile.py", "w") as f:
       transformer.dump(f, ["my_har_files_directory/"])

Documentation
=============

Take a look at our documentation_ for more details, including how to **generate
HAR files**, **customize your scenarios**, use or write **plugins**, etc.

.. _documentation: https://transformer.readthedocs.io/

Authors
=======

- **Serhii Cherniavskyi** — `@scherniavsky <https://github.com/scherniavsky>`_

- **Thibaut Le Page** — `@thilp <https://github.com/thilp>`_

- **Brian Maher** — `@bmaher <https://github.com/bmaher>`_

- **Oliwia Zaremba** — `@tortila <https://github.com/tortila>`_

See also the list of contributors_ to this project.

.. _contributors: https://transformer.readthedocs.io/en/latest/Contributors.html

License
=======

This project is licensed under the MIT license — see the LICENSE.md_ file for
details.

.. _LICENSE.md: https://github.com/zalando-incubator/Transformer/blob/master
   /LICENSE.md

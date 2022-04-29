.. _ignoring-urls:

🙈🙉 Ignoring specific URLs
===========================

By default, Transformer converts *all* requests found in the HAR files you
provide.
However, you can **ignore** certain URLs by creating a
``.urlignore`` file in the directory in which Transformer is executed.

Example
-------

A ``.urlignore`` containing::

   google
   www.facebook.com
   https://mosaic

... would ignore requests with URLs such as:

- ``https://www.google.com``,
- ``https://www.facebook.com/``,
- ``https://mosaic01-abc.js``,
- ... and more following the same patterns.

We provide an example denylist file called `.urlignore_example`_ that you can
use as a base.
Note that it needs to be **renamed** ``.urlignore`` for Transformer to take it
into account.

.. _.urlignore_example: https://github.com/zalando-incubator/Transformer/blob/master/transformer/.urlignore_example

.. _ignoring-urls:

🙈🙉 Ignoring specific URLs
===========================

By default, Transformer converts *all* requests found in the HAR files you
provide.
However, you can **ignore** certain URLs by creating an
``.ignore`` file in the directory in which Transformer is executed.

The file supports regular expressions.

Example
-------

An ``.ignore`` file containing::

   google
   https://mosaic
   .*/foo.gif

... would ignore requests with URLs such as:

- ``https://www.google.com``,
- ``https://mosaic01-abc.js``,
- ``https://anything.com/foo.gif``,
- ... and more following the same patterns.

We provide an example denylist file called `.ignore_example`_ that you can
use as a base.
Note that it needs to be **renamed** ``.ignore`` for Transformer to take it
into account.

.. _.ignore_example: https://github.com/zalando-incubator/Transformer/blob/master/transformer/.ignore_example

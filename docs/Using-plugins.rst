.. _using-plugins:

🔌 Using Plugins
================

Transformer's conversion between HAR and locustfile is **very simple**:
at its core, it just wraps each HTTP request (from the HAR file) with
a call to the requests_ library in the class definitions expected by Locust.

.. _requests: http://docs.python-requests.org/en/master/

.. figure:: _static/basic-conversion.*
   :align: center

   *What Transformer does (simplified).*

**Anything more complex** has to happen via the **plugin system**.
Thanks to this separation, we keep Transformer's core small and generic,
and users easily add the features they need without having to fork Transformer
and learn about its internals.

.. contents::
   :local:

Where to find plugins
---------------------

Plugins come from different sources:

- Some of them ship with Transformer itself: for instance, `Sanitize Headers`_
  is so useful that it is enabled by default.
- Others can be distributed on PyPI: plugins are regular Python modules, so
  they can be shared and reused like any library.
  We recommend plugin authors to stick to the convention of naming their
  plugins with the ``har-transformer-plugin-`` prefix, so that they are easily
  discoverable.
- What is still missing can simply be implemented by *you*.
  The :ref:`writing-plugins` section explains how to do this.

.. _Sanitize Headers: https://github.com/zalando-incubator/Transformer/blob/master/transformer/plugins/sanitize_headers.md

How to use a specific plugin
----------------------------

**Plugins are normal Python modules**, so they have an **identifier**.
For instance, the identifier of the `Sanitize Headers`_ plugin is
``transformer.plugins.sanitize_headers``, which is the name of `the module
where it is defined <https://github.com/zalando-incubator/Transformer/blob/master/transformer/plugins/sanitize_headers.py>`_.
(You would usually not explicitly enable *Sanitize Headers*, since it is
enabled by default -- it just serves as an example here).

When you know the name of a plugin, you can tell Transformer to use it either
with the ``transformer`` command-line tool, or with functions made available by
the Transformer library.

Command-line usage
""""""""""""""""""

Use the :option:`-p`/:option:`--plugin` option with the identifier of the
plugin you want::

   $ transformer -p transformer.plugins.sanitize_headers ...

Specify that option multiple times (with appropriate plugin identifiers) to
enable all corresponding plugins.

Library usage
"""""""""""""

Use the :func:`dump` or :func:`dumps` function and provide the names of the
plugins you want to use as the *plugins* argument:

.. code-block:: py

   import sys
   import transformer

   har_paths = [...]
   transformer.dump(
      sys.stdout,
      har_paths,
      plugins=["transformer.plugins.sanitize_headers"]
   )

Plugin examples
---------------

- Shipping with Transformer (under ``transformer.plugins.*``):

  - `Sanitize Headers`_: Remove Chrome-specific pseudo-headers not actually
    exchanged with the target, but added to the HAR file by the recording tool.

- Implemented for our needs at Zalando:

  - Convert a specific incoming cookie into a header sent with each outgoing
    request.

  - Emit `OpenTracing spans`_ in all outgoing requests.

  - Extract an ID from some real incoming response and insert it in a
    placeholder in a subsequent outgoing request.

.. _OpenTracing spans: https://opentracing.io/docs/overview/spans/

.. seealso::

  :ref:`writing-plugins`
    How to write your own Transformer plugins.

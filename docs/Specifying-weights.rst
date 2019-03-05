.. _specifying-weights:

⚖ Specifying Weights
====================

By default, Transformer considers that all scenarios have the same weight 1,
which means they should all be executed as often as the others.

You can specify a **different weight for each HAR file** by creating
an **associated weight file**.
For example, to give a weight to the ``abc.har`` scenario, create
a ``abc.weight`` file in the same directory.
``abc.weight`` should contain the weight you want to associate to ``abc.har``,
like ``2`` or ``76``.

.. note::

   Weights must be positive, non-null **integers** due to how Locust works.

Consider the following group of scenario files displayed in a shell:

.. code-block:: sh

   $ ls
   scenario1.har
   scenario2.har
   scenario2.weight

   $ cat scenario2.weight
   3

Here are the weights Transformer will specify in the corresponding locustfile:

================= ======
Scenario          Weight
================= ======
``scenario1.har``    1
``scenario2.har``    3
================= ======

This means that Locust will run ``scenario2.har`` **three times as much** as
``scenario1.har``.

.. seealso::

   :ref:`hierarchical-scenarios`
      If you have *groups* of scenarios that *taken together* should have
      a weight compared to other *groups* (instead of *per-scenario* weights).

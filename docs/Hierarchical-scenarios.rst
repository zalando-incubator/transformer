.. _hierarchical-scenarios:

👑 Hierarchical Scenarios
=========================

It may be the case that all your scenarios cannot be treated the same:

- some only apply to *a part* of your load test target,
- some should run *more often* than others.

For instance, the Zalando website works differently depending on its top-level
domain: zalando.\ **fr** has an additional step before payment compared to
zalando.\ **de**.
This requires using different scenarios (i.e. different HAR files) depending on
the tested domain.
Moreover, to execute a *realistic* load test, we need to produce much more
traffic targeting certain countries than others.

.. _weight: Specifying-weights.html

To accomodate this way of working, our HAR files are organized in
country-specific directories, each of which is potentially associated to a
specific `weight`_ according to the relative amount of traffic expected::

    scenarios/
    ├── Germany/
    │   ├── scenario_1.har
    │   ├── scenario_2.har
    │   └── scenario_2.weight
    ├── Germany.weight
    ├── Switzerland/
    │   └── scenario_1.har
    └── Switzerland.weight

The weight files of directories (``Germany.weight``, ``Switzerland.weight``) are
similar to `scenario weight files <Specifying-weights.html>`_ but apply to the
whole directory (relatively to other directories of the same level).
Thus, in the previous example, if ``Germany.weight`` is ``6`` and
``Switzerland.weight`` is ``2``, then Germany scenarios will be executed
(in total) three times more (6 / 2) than Switzerland scenarios.

Just like for HAR files, a directory without a weight file has a default weight
of 1.

.. _hierarchical-example:

Scenarios can be arbitrarily nested, allowing you to organize and weight them
as you want::

    scenarios/
    ├── Germany/
    │   ├── beauty/
    │   │   └── checkout.har
    │   ├── kids/
    │   │   └── frontpage.har
    │   ├── kids.weight
    │   └── scenario_1.har
    ├── Germany.weight
    ├── Switzerland/
    │   └── scenario_1.har
    └── Switzerland.weight

To represent this, Transformer will produce `nested Locust TaskSets`_ in the
resulting locustfile.

.. _nested Locust TaskSets:
    https://docs.locust.io/en/stable/writing-a-locustfile.html#tasksets-can-be-nested

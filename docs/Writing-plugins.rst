.. _writing-plugins:

🚀 Writing plugins
==================

If the plugins that come with Transformer (or that you find on PyPI) don't
cover your use-cases, you can easily implement and use your *own* plugins.

.. contents::
   :local:

High-level design
-----------------

Transformer converts data from a HAR file into a locustfile:

.. figure:: _static/design-simple.*
   :align: center

Internally, the HAR data is first converted into an *intermediate data
structure*, which is easier to manipulate than both JSON (from HAR files) and
Python code (of a locustfile).
We can zoom in the "Transformer" part of the above diagram to see it
(it's called "internal objects"):

.. figure:: _static/design-internal-objects.*
   :align: center

These internal objects belong to one of the following categories:

.. glossary::

   Task
      What you put in a simple Locust :class:`TaskSet <locust.core.TaskSet>`:
      an atomic action, represented by a simple HTTP request and some
      pre-/post-processing code.

   Scenario
      How are organized your HAR files, for instance the :ref:`per-country,
      per-segment hierarchy we used at Zalando <hierarchical-example>`.
      A scenario is a tree_ containing :term:`tasks <task>` or more specific
      scenarios.

   Syntax tree
      Towards the end of the Transformer conversion, :term:`tasks <task>` and
      :term:`scenarios <scenario>` are converted into "abstract" Python code
      but not yet represented as text: it's a `syntax tree`_.
      At this stage, any part of the future locustfile can be modified by
      manipulating the syntax tree.
      Later, this syntax tree will be converted into concrete Python code
      written with actual text in the locustfile.

.. _Locust TaskSet: https://docs.locust.io/en/stable/writing-a-locustfile.html#taskset-class
.. _tree: https://en.wikipedia.org/wiki/Tree_(data_structure)
.. _syntax tree: https://en.wikipedia.org/wiki/Abstract_syntax_tree

Plugins are pieces of code that modify these internal objects before
Transformer converts them into a locustfile:

.. figure:: _static/design-plugins.*
   :align: center

Depending on what a plugin has to do, it will modify a specific subset of these
internal objects.
For example, an authentication plugin could target only :term:`tasks <task>`
that make requests to a specific URL.
It would not need to modify :term:`scenario` objects or the :term:`syntax tree`
directly.

.. warning::

   Modifying :any:`har_entry <transformer.request.Request.har_entry>` property
   of a :class:`Request <transformer.request.Request>` object will not have any effect on the resulting
   :term:`task`. The field serves the purpose of exposing all data recorded in a HAR file corresponding
   to the specific :class:`Request <transformer.request.Request>`, that might have otherwise not been reflected
   in the intermediate representation.

To let Transformer know that this authentication plugin must be executed with
:term:`task` objects passed as input (and not, say, :term:`scenario` objects),
the plugin's author must announce that **the plugin satisfies a specific
contract**: in this case, the :term:`OnTask` contract.
Other contracts exist for other categories of internal objects, and can be
combined for plugins that interact with several of these categories.

.. _contracts:

Contracts
---------

Transformer plugins are just (decorated) Python functions.
As such, they accept certain inputs and have certain outputs.

However, not all plugins can be applied at the same point in Transformer's
pipeline.
For example, :term:`task` objects don't exist at the same time as
:term:`syntax tree` objects.

That is the reason for having different **contracts**, which plugin authors use
to announce to which objects their plugin should have access.
Thanks to a plugin's contract, Transformer knows *when* to invoke the plugin
and *what* objects to pass it.

Basic Contracts
'''''''''''''''

.. glossary::

   OnTask
      Category of plugins that operate independently on each :term:`task`.

      When implementing this contract with a plugin, imagine that plugin could be
      applied concurrently to all tasks by Transformer in the future, with no
      determined order.
      If you only need to modify, say, the first task of each :term:`scenario`,
      then you should use the :term:`OnScenario` contract rather than *OnTask*.

      **Example:** A plugin that injects a header in all requests.

   OnScenario
      Category of plugins that operate on each :term:`scenario`.

      Each scenario is the root of a tree composed of smaller scenarios and
      :term:`tasks <task>` (the leaves of this tree).
      Therefore, in an *OnScenario* plugin, you have the possibility of
      **inspecting the subtree** and making decisions based on that.

      .. warning::

         *OnScenario* plugins are be applied to all scenarios by Transformer,
         so **you don't need to recursively apply the plugin** yourself on all
         subtrees.
         If you do that, the plugin will be applied many more times than
         necessary.

      **Example:** A plugin that keeps track of how long each scenario runs.

   OnPythonProgram
      Category of plugins that operate directly on the whole :term:`syntax
      tree`.

      The input and output of these plugins is the complete locustfile
      generated by Transformer, represented as a :term:`syntax tree`.
      They therefore have the most freedom compared to other plugin categories,
      because they can change *anything*.

      Their downside is that the syntax tree is more complex to manipulate than
      the scenario tree or individual tasks.

      **Example:** A plugin that injects some code in the global scope.

Composite Contracts
'''''''''''''''''''

Multiple basic contracts can be combined into a new contract.

For example, if a contract *C* is a combination of contracts *A* and *B*,
then a plugin announcing it implements *C* announces it implements both *A* and
*B*.

In practice, Transformer contracts are members of :class:`Contract
<transformer.plugins.Contract>`, an :class:`enum.Flag`, which allows to combine
them using the ``|`` operator.

Implementation details
----------------------

Technically, a Transformer plugin is a **Python function** *F* in a **module**
*M* and that announces a **contract** *C*.

The **name** or **identifier** of the plugin (as provided to Transformer) is
actually the **qualified name** of the module *M*.
See :ref:`name-resolution` below for details.

To announce its contract, the plugin function *F* is **decorated** with
:any:`@plugin <transformer.plugins.plugin>` and the appropriate contract *C*,
which is a member of the :class:`Contract <transformer.plugins.Contract>` enum:

.. code-block:: py

   from transformer.plugins import Contract, plugin

   @plugin(Contract.OnTask)
   def my_plugin(t: Task) -> Task:
      ...

Here the contract *C* is :term:`OnTask`, which makes the plugin receive all
internal objects of category :term:`Task` one-by-one.

.. note::

   The module *M* can contain **other functions**: if they are not decorated
   with :any:`@plugin <transformer.plugins.plugin>`, they will *not* be
   considered Transformer plugins, but they can still be used by a function
   that is a plugin.

.. note::

   You can also have **multiple** :any:`@plugin
   <transformer.plugins.plugin>`-decorated functions in the same module *M*:
   they will all be plugins **with the same name**.

   However, their relative order of execution will be unspecified.
   For that reason, if multiple plugins should be executed one after the other
   in a specific order, they should be **implemented in different modules**,
   so that users can specify the order themselves when providing the plugin
   names to Transformer.

.. _name-resolution:

Name resolution
---------------

Let's say we have a :file:`mod/sub.py` file containing the definition of
a plugin function called ``my_plugin`` as in the previous section.

Let's also assume that your Python import path is configured so that you can
execute ``from mod.sub import my_plugin`` successfully.

You can use this custom plugin by :ref:`passing its name to Transformer
<using-plugins>`.
Your plugin's name is **not** the name of the function (``my_plugin`` or
``mod.sub.my_plugin``) but the name of the module containing its definition,
i.e. just ``mod.sub``.

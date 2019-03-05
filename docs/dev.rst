⚙ Technical documentation
=========================

.. contents::
   :local:

.. automodule:: transformer
   :members:

.. automodule:: transformer.plugins

   .. seealso::

      :ref:`writing-plugins`
         The rationale for contracts, and a description of the most important
         ones.

   .. decorator:: plugin(contract)

      Associates a function to a :class:`Contract`, making that function
      a Transformer plugin that will be detected as such by
      :func:`resolve <transformer.plugins.resolve.resolve>`.

      :param Contract contract: the contract to associate to the decorated
         function.
      :raise InvalidContractError: if *contract* is not a valid
         :class:`Contract`.

   .. autoclass:: Contract
      :members:
      :undoc-members:
      :member-order: bysource

   .. data:: Plugin

      Subtype of functions (:any:`callable`) that are registered as Transformer
      plugins.
      Mostly useful in type annotations.

.. automodule:: transformer.request
   :members:

.. automodule:: transformer.task
   :members: Task2

.. automodule:: transformer.scenario
   :members: CollidingScenariosError, DanglingWeightError,
      SkippableScenarioError, WeightValueError

   .. autoclass:: Scenario
      :members: from_path

.. automodule:: transformer.python
   :members:
   :show-inheritance:
   :member-order: bysource

   .. seealso::

      :term:`Syntax tree`
         High-level description of Transformer's "syntax tree" internal object.

   .. data:: Program

      A |Sequence| of |Statement| objects.
      Useful as alias in type signatures.

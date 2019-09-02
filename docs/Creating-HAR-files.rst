🌱 Creating HAR files
=====================

`HAR`_ files are `JSON`_ files storing everything needed to "replay"
a web browsing session from the server's point of view.
They contain all web requests made by a `web browser`_, and the corresponding
responses from the server.

.. _HAR: https://en.wikipedia.org/wiki/.har
.. _JSON: https://en.wikipedia.org/wiki/JSON
.. _web browser: https://en.wikipedia.org/wiki/Web_browser

For this reason, we often call a HAR file **a scenario**: like the scenario of
a play or movie, it describes what is supposed to happen.
Following a scenario is experiencing the story it tells.

Transformer converts these HAR files into a program that `load tests`_
the visited web sites by **replaying** the recorded scenarios at large scale.

.. _load tests: https://en.wikipedia.org/wiki/Load_testing

**Anyone can easily create HAR files using a web browser.**
Here, we use Chrome, but the steps for Firefox are extremely similar (and other
browsers probably follow the same pattern).

Record a scenario
-----------------

#. **Prepare your scenario** by thinking through the steps you want to execute.
#. Open Chrome in either **Guest** or **Incognito** mode (it's important to have
   no cookies prior to starting).
#. Open the `Developer Tools`_.
#. Open the **Network** panel.
#. Select **Disable cache** and **Preserve log**.
#. Clear the existing log by clicking the **Clear** 🚫 button.
#. Ensure recording is enabled: the **Record** button should be red 🔴 (click it
   to toggle).
#. **Navigate** to your target site by entering the URL in the address bar, like
   ``https://www.zalando.de``.
#. **Perform your scenario** by clicking through the pages, filling in forms,
   clicking buttons, etc.

.. _Developer Tools: https://developers.google.com/web/tools/chrome-devtools/network-performance/

.. note::

   After each click/action, and before the next one, we recommend that you wait
   until the network panel stops showing activity.
   This ensures that all requests are properly recorded.

Save your scenario as HAR
-------------------------

Once you have finished performing your scenario:

#. **End recording** by clicking the Record 🔴 button.
#. **Right-click** on any of the file names listed in the bottom pane of the
   Network panel.
#. Select **Save as HAR with content**.
#. Save the file on your machine.

.. note::

   You can view the details of a HAR file by simply drag-and-dropping it into
   the Chrome Developer Tools Network panel.

.. seealso::

   :ref:`specifying-weights`
      Define how often should a particular scenario be executed compared to the
      others.

   :ref:`hierarchical-scenarios`
      Organize your groups of scenarios.

   :ref:`ignoring-urls`
      Avoid including irrelevant URLs from your HAR files into the final
      locustfile.

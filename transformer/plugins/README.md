# Plugins

<!-- toc -->

- [List of available plugins](#list-of-available-plugins)
- [How to use plugins](#how-to-use-plugins)
  * [From the command-line](#from-the-command-line)
  * [When using Transformer as a library](#when-using-transformer-as-a-library)
- [Writing custom plugins](#writing-custom-plugins)
  * [Implementation](#implementation)
  * [Name resolution](#name-resolution)

<!-- tocstop -->

## List of available plugins

[sanitize_headers]: sanitize_headers.md

  - [`transformer.plugins.sanitize_headers`][sanitize_headers] - used by default

## How to use plugins

### From the command-line

Use the `-p`/`--plugin` command-line option associated to a plugin name
(possibly repeatedly):

```bash
$ transformer -p transformer.plugins.sanitize_headers ...
```

Use `transformer --help` or just `transformer` for more details about
the command-line documentation.

### When using Transformer as a library

Use the `dump` or `dumps` method and provide the names of the plugins you want
to use as the `plugins` argument:

```python
from sys import stdout
import transformer

scenarios = [...]
transformer.dump(stdout, scenarios, plugins=["transformer.plugins.sanitize_headers"])
```

Note that the above example only aims to illustrate how to use a plugin.
There's no need to specifically use the `sanitize_headers` plugin,
because it's used by default anyway.

## Writing custom plugins

If the plugins that come with Transformer or that you can find on PyPI don't
cover your use-cases, you can implement and use your own plugin.

### Implementation

A Transformer plugin is a Python function with a specific constraints:

  - its name must begin with `plugin` (examples: `plugin`, `plugin_x`);
  - it must use Python's [type hints syntax](https://www.python.org/dev/peps/pep-0484/);
  - its parameters and return value (as specified by its type hints) must match
    those defined by [one of the _Plugin_ subtypes](contracts.py).

See the [`sanitize_headers`][] plugin as an example.

### Name resolution

Let's say the `mod/sub.py` file contains a function called `plugin_f`
implementing the constraints listed in the previous section.

Let's also assume that your Python import path is configured so that you can
execute `from mod.sub import plugin` successfully.

You can use this custom plugin by passing its name to Transformer.
Your plugin's name is **not** the name of the function (`plugin_f`)
but the name of the module containing it (`mod.sub`).

This means that you can have multiple "plugin functions" (`plugin_f`,
`plugin_postprocessing`, etc.) under the same plugin name.

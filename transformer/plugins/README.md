# Plugins

## List of available plugins

- [`sanitize_headers`](sanitize_headers.md)

## How to use plugins

In order to use a plugin, pass a method of a [`Plugin`](__init__.py) signature:
- a single argument of type `Sequence[Task]`
- returned value of type `Sequence[Task]`

to the `transform.main` function like so:
```python
from transformer import transform
from transformer.plugins import sanitize_headers

paths = [...]
locustfile = transform.main(paths, plugins=[sanitize_headers.plugin])
```

[`Plugin`]: __init__.py
[`sanitize_headers`]: sanitize_headers.py

## Writing custom plugins

It's possible to use custom plugins. A valid plugin must be a method with the signature of the [`Plugin`][].

Each plugin has access to all `Task`s that are generated from the HAR file, and can modify them in different way,
depending on the intent:
- the `locust_request` attribute can be modified in order to change the request itself, e.g. its URL or parameters,
- the `locust_preprocessing` attribute can be modified in order to add some logic **before** the request,
- the `locust_postprocessing` attribute can be modified in order to add some logic **after** the request;
  at this stage, the `response` object from the request can also be used.

Each plugin must take a full collection of tasks (`Sequence[Task]`) as argument, and return it as well,
which means that both: modified and untouched tasks should be returned, with respect to their order.

See [`sanitize_headers`][] plugin as an example of the implementation.

<p align="center"><img src="images/transformer.png"/></div>

# Transformer

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/06e990f6de394960a67dbc5a39a76d84)](https://app.codacy.com/app/thilp/Transformer?utm_source=github.com&utm_medium=referral&utm_content=zalando-incubator/Transformer&utm_campaign=Badge_Grade_Dashboard)


A tool to transform/convert web browser sessions ([HAR files][]) into
[Locust][] load testing scenarios (locustfile).

This tool can be used when you have HAR files (containing recordings of
interactions with your website) that you then want to replay in load tests
using Locust.

[HAR files]: https://en.wikipedia.org/wiki/.har
[Locust]: https://locust.io/

## Prerequisites

- [Python][]
- [pipenv][]

[Python]: https://www.python.org/
[pipenv]: https://pipenv.readthedocs.io/en/latest/

## Usage

Install as editable dependency with pipenv:

```bash
$ pipenv install -e local/path/to/transformer
```

Import in your code and use it:
```python
from transformer import transform

with open("locustfile.py", "w") as locust_file:
  locust_file.write(transform.main("scenarios_directory/"))
```

Example HAR files are included in the `examples` directory for you to try out.

## How-to

### Create a HAR file

#### Using Chrome Developer Tools

__Record__

1. __Prepare your scenario__ by thinking through the steps you want to execute
2. Open __Chrome__ in either __Guest__ or __Incognito__ mode (it's important to have no cookies prior to starting)
3. Open the [Developer Tools][]
4. Open the __Network__ panel
5. Select __Disable cache__ and __Preserve log__
6. Clear the existing log by clicking the __Clear__ :no_entry_sign: button
7. Ensure recording is enabled, the __Record__ button should be red  :red_circle: (click to toggle)
8. __Navigate__ to your target site by entering the URL in the address bar e.g. https://www.zalando.de, https://www.zalando.de/damen-home/, etc.
9. __Perform your scenario__ by clicking through the pages, filling in forms, clicking buttons etc.

__N.B.__ It's recommend that after each click/action, and before the next one, you wait until the network panel stops showing activity. This is to ensure that all requests are properly recorded.

[Developer Tools]: https://developers.google.com/web/tools/chrome-devtools/network-performance/

__Save__

Once you have finished performing your scenario:

1. __End recording__ by clicking the Record :red_circle: button
2. __Right-click__ on any of the file names listed in the bottom pane of the Network panel
3. Select __Save as HAR with content__
4. __Save__ the file on your machine

ℹ️  _You can view the details of the recorded HAR by simply drag-and-dropping it into the Chrome Developer Tools Network panel._

### Scenario weights

By default, all scenarios have the same weight 1, which means they should all be
executed as often as the others.

You can specify a different weight for each HAR file by creating an associated
weight file. Weights must be positive, non-null integers due to how Locust works.
Consider the following scenario group:

```bash
$ ls
scenario1.har
scenario2.har
scenario2.weight

$ cat scenario2.weight
3
```

Here are the weights Transformer will specify in the corresponding locustfile:

| Scenario        | Weight |
| --------------- | ------ |
| `scenario1.har` | 1      |
| `scenario2.har` | 3      |

This means that Locust will run `scenario2.har` 3 times as much as
`scenario1.har`.

### Hierarchical scenarios

It may be the case that all your scenarios cannot be treated the same:

- some only apply to a part of your load test target,
- some should run more often than others.

For instance, the Zalando website works differently depending on its top-level
domain: zalando.fr has an additional step before payment compared to zalando.de.
This requires using different scenarios (i.e. different HAR files) depending on
the tested domain.
Moreover, to execute a realistic load test, we need to produce much more traffic
targeting certain countries (i.e. groups of scenarios) than others.

To accommodate this way of working, our HAR files are organized in TLD-specific
directories, each of which is potentially associated to a specific "weight"
according to the relative amount of traffic expected:

```
scenarios/
├── Germany/
│   ├── scenario_1.har
│   ├── scenario_2.har
│   └── scenario_2.weight
├── Germany.weight
├── Switzerland/
│   └── scenario_1.har
└── Switzerland.weight
```

The "weight file" of directories (`Germany.weight`, `Switzerland.weight`) are
similar to [scenario weight files](#scenario-weights) but apply to the whole
directory (relatively to other directories of the same level).
Thus, in the previous example, if `Germany.weight` is `6` and
`Switzerland.weight` is `2`, then Germany scenarios will be executed (in total)
3 times more (6 / 2) than Switzerland scenarios.
A directory without a weight file has a weight of 1.

Scenarios can be arbitrarily nested, allowing you to organize and weight them as
you want:

```
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
```

To represent this, Transformer will produce nested
[Locust TaskSets](https://docs.locust.io/en/stable/writing-a-locustfile.html#tasksets-can-be-nested)
in the resulting locustfile.

### Blacklist specific URLs

By default, Transformer converts all requests found in input HAR files.
You can blacklist, i.e. ignore, certain URLs by creating a `.urlignore` file in the directory
in which Transformer is called.

__Example__

A `.urlignore` containing:
```
google
www.facebook.com
https://mosaic
```

... would ignore requests with URLs such as `https://www.google.com`, `https://www.facebook.com/`, and
`https://mosaic01-abc.js` (amongst others).

An example blacklist file called [`.urlignore_example`](transformer/.urlignore_example) exists
that you can use as a base.

### Use plugins

In case you need some customization of the Locustfile generated by Transformer, you can use its plugin
mechanisms to achieve it. Please see [`plugins` documentation](transformer/plugins) for more details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our process for submitting pull requests to us, and please ensure
you follow the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/zalando-incubator/transformer/tags).

## Development

### Install dependencies

```bash
pipenv install --dev
```

### Run tests

Single-run
```bash
pipenv run pytest
```

ℹ️  _Using [pytest](https://docs.pytest.org/en/latest/), [mock](https://docs.python.org/3/library/unittest.mock.html), and [Hypothesis](https://hypothesis.readthedocs.io/en/latest/).

### Run linter

```bash
pipenv run pylint ./*.py
```

ℹ️  _Using [Pylint](https://www.pylint.org/)._

## Authors

* **Serhii Cherniavskyi** - [@scherniavsky](https://github.com/scherniavsky)
* **Thibaut Le Page** - [@thilp](https://github.com/thilp)
* **Brian Maher** - [@bmaher](https://github.com/bmaher)
* **Oliwia Zaremba** - [@tortila](https://github.com/tortila)

See also the list of [contributors](CONTRIBUTORS.md) who participated in this project.

## License

This project is licensed under the MIT License - see the
[LICENSE.md](LICENSE.md) file for details.

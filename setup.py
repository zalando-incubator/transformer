# pylint: skip-file

import os

import setuptools

MODULE_DIR = os.path.dirname(__file__)
README = os.path.join(MODULE_DIR, "README.md")
REQUIREMENTS = os.path.join(MODULE_DIR, "requirements.txt")

with open(README) as readme:
    long_description = readme.read()

with open(REQUIREMENTS) as req_file:
    requirements = [line for line in req_file.read().splitlines() if "==" in line]

version = os.environ.get("CDP_BUILD_VERSION", "dev")
if "master-" in version:
    version = version.split("-")[1]
elif "pr-" in version:
    version = f"dev{version.split('-')[1]}+{version.split('-')[2]}"


def version() -> str:
    # https://packaging.python.org/guides/single-sourcing-package-version/
    h = {}
    with open("transformer/__version__.py") as f:
        exec(f.read(), h)
    return h["__version__"]


setuptools.setup(
    name="transformer",
    version=version(),
    author="Team Tip",
    author_email="team-tip@zalando.de",
    description="Transforms HAR to Locustfile",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zalando-incubator/Transformer",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=["Programming Language :: Python :: 3"],
    entry_points={
        "console_scripts": ["transformer = transformer.cli:script_entrypoint"]
    },
)

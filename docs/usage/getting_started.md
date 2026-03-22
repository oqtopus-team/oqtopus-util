# Getting Started

OQTOPUS Util is a collection of utility libraries designed to standardize common tasks—such as configuration management and dependency injection—within the quantum computing platform ecosystem.

## Prerequisites

Python Version: Python 3.11 or higher is required.

## Installation

You can install `oqtopus-util` using `pip`:

```shell
pip install oqtopus-util
```

If you are using `uv` for package management, we recommend the following:

```shell
uv add oqtopus-util
```

## Features

| Features                          | Description |
| --------------------------------- | ----------- |
| [Config Util](./config_util.md)   | Loads YAML configs with env-var substitution, sensitive value masking, and logging setup. |
| [DI Container](./di_container.md) | A configuration-based DI container that swaps implementations without code changes. |

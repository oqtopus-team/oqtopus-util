# DI Container

`oqtopus_util.di` provides a lightweight, configuration-based Dependency Injection (DI) container. It allows you to swap object implementations without modifying your source code by instantiating and managing Python objects directly from a YAML-based configuration.

## Overview

The `DiContainer` class reads a registry configuration (a plain Python `dict`, typically
produced by [`load_config`](./config_util.md)) and creates objects on demand.

By simply changing the configuration file, you can switch between different implementations (e.g., switching from a simulator to a real quantum device) without touching the application logic.

Each top-level key in the registry identifies a **component**.
The component configuration must contain a `_target_` key with the fully-qualified
class path.

| Key | Required | Description |
| --- | --- | --- |
| `_target_` | Yes | Fully-qualified class path (e.g. `mypackage.module.MyClass`) |
| `_scope_` | No | `singleton` (default) or `prototype` |
| other keys | — | Passed as keyword arguments to the class constructor |

String values that start with `@` are treated as **dependency references** and are
resolved recursively before being passed to the constructor.

## Basic Usage

### 1. Define a registry in YAML

```yaml
registry:
  job_fetcher:
    _target_: myapp.fetchers.JobFetcher
    _scope_: singleton
    repo: "@job_repo"

  job_repo:
    _target_: myapp.repositories.JobRepository
    base_url: "http://localhost:8888"
```

### 2. Load the registry and create the container

```python
from oqtopus_util.config import load_config
from oqtopus_util.di import DiContainer

registry = load_config("config/registry.yaml")
container = DiContainer(registry)
```

### 3. Retrieve components

```python
fetcher = container.get("job_fetcher")
# fetcher is an instance of myapp.fetchers.JobFetcher.
# Its "repo" argument was resolved automatically to a JobRepository instance.
```

## Scopes

### singleton (default)

The container creates the instance once and returns the same object on every subsequent
call to `get()`.

```python
a = container.get("job_fetcher")
b = container.get("job_fetcher")
assert a is b  # True — same instance
```

### prototype

A new instance is created on every call to `get()`.

```yaml
registry:
  job_fetcher:
    _target_: myapp.fetchers.JobFetcher
    _scope_: prototype
```

```python
a = container.get("job_fetcher")
b = container.get("job_fetcher")
assert a is not b  # True — different instances
```

## Dependency References

A string value that starts with `@` refers to another component in the registry.
References are resolved recursively, so chains of dependencies are supported.

```yaml
registry:
  service:
    _target_: myapp.Service
    repo: "@repository"

  repository:
    _target_: myapp.Repository
    db: "@database"

  database:
    _target_: myapp.Database
    url: "postgresql://localhost/mydb"
```

```python
service = container.get("service")
# DiContainer resolves: service → repository → database
#                        service → app_logger
```

## Error Handling

| Situation | Exception raised |
| --- | --- |
| Component name not found in registry | `KeyError` |
| `_target_` key is missing | `ValueError` |
| Module or class cannot be imported | `ImportError` |
| Constructor arguments do not match | `TypeError` |
| Circular dependency detected | `CircularDependencyError` |

### CircularDependencyError

`CircularDependencyError` is a subclass of `ValueError` and is raised when two or more
components depend on each other in a cycle.

```python
from oqtopus_util.di import CircularDependencyError

try:
    container.get("component_a")
except CircularDependencyError as exc:
    print(exc)  # "Circular dependency detected: component_a -> component_b -> component_a"
```

## load_class

`oqtopus_util.di` also exports the `load_class` helper function, which dynamically
imports a class from a fully-qualified path string.

```python
from oqtopus_util.di import load_class

MyClass = load_class("mypackage.module.MyClass")
instance = MyClass()
```

## Complete Example

### Project structure

```text
myapp/
  __init__.py
  service.py
config/
  di.yaml
main.py
```

### myapp/service.py

```python
class Repository:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

class Service:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def run(self) -> str:
        return f"connected to {self.repo.base_url}"
```

### config/di.yaml

```yaml
registry:
  service:
    _target_: myapp.service.Service
    repo: "@repository"

  repository:
    _target_: myapp.service.Repository
    base_url: "http://localhost:8888"
```

### main.py

```python
from oqtopus_util.config import load_config
from oqtopus_util.di import DiContainer

config = load_config("config/di.yaml")
dicon = DiContainer(**config)

service = dicon.get("service")
print(service.run())  # "connected to http://localhost:8888"
```

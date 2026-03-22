# Config Util

`oqtopus_util.config` provides utility functions for loading YAML configuration files
with environment-variable substitution, masking sensitive values, and applying logging
configuration.

## Functions

### load_config

```python
from oqtopus_util.config import load_config

config = load_config("config/config.yaml")
```

`load_config(config_path)` reads a YAML file and returns a Python `dict`.

Before the file is parsed by PyYAML, every `${VAR}` and `${VAR, default}` placeholder
is replaced at the string level, allowing YAML to apply its own type-casting rules.

| Placeholder | Environment variable set | Result |
| --- | --- | --- |
| `${VAR}` | Yes | Raw value of `VAR` (string; YAML casts the surrounding context) |
| `${VAR}` | No | `null` (YAML `None`) |
| `${VAR, default}` | Yes | Raw value of `VAR` |
| `${VAR, default}` | No | `default` — YAML type-casts it (e.g. `10` → `int`, `false` → `bool`) |

String values that start with `~` are expanded to absolute home-directory paths
(equivalent to `Path(value).expanduser()`).

#### Example config.yaml

```yaml
server:
  host: ${HOST, localhost}
  port: ${PORT, 8080}
  debug: ${DEBUG, false}
  data_dir: ~/oqtopus/data
```

```python
import os
from oqtopus_util.config import load_config

os.environ["HOST"] = "example.com"

cfg = load_config("config/config.yaml")
# cfg["server"]["host"]     == "example.com"
# cfg["server"]["port"]     == 8080          (int, cast by YAML)
# cfg["server"]["debug"]    is False         (bool, cast by YAML)
# cfg["server"]["data_dir"] == "/home/user/oqtopus/data"
```

### mask_sensitive_info

```python
from oqtopus_util.config import mask_sensitive_info

safe_cfg = mask_sensitive_info(config)
```

`mask_sensitive_info(config)` returns a copy of the configuration dictionary where
the values of the following keys are replaced with `"***MASKED***"`:

- `api_token`
- `password`
- `secret_key`

The function processes nested dictionaries recursively, so sensitive values at any depth
are masked.

#### Example

```python
from oqtopus_util.config import mask_sensitive_info

config = {
    "database": {
        "host": "localhost",
        "password": "s3cr3t",
    },
    "api_token": "abc123",
}

safe = mask_sensitive_info(config)
# safe["database"]["password"] == "***MASKED***"
# safe["api_token"]            == "***MASKED***"
# safe["database"]["host"]     == "localhost"
```

### setup_logging

```python
from oqtopus_util.config import setup_logging

setup_logging(logging_cfg)
```

`setup_logging(logging_cfg)` applies a logging configuration dictionary by calling
[`logging.config.dictConfig`](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig).

The `logging_cfg` argument must be a Python `dict`.
A `TypeError` is raised if a non-dict value is passed.

#### Example

```python
from oqtopus_util.config import load_config, setup_logging

logging_cfg = load_config("config/logging.yaml")
setup_logging(logging_cfg)
```

#### Example logging.yaml

```yaml
version: 1
formatters:
  default:
    format: "%(asctime)s %(levelname)s %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
    stream: ext://sys.stdout
root:
  level: INFO
  handlers: [console]
disable_existing_loggers: false
```

## Complete Example

```python
import logging
from oqtopus_util.config import load_config, mask_sensitive_info, setup_logging

# Load main configuration
config = load_config("config/config.yaml")

# Set up logging first
logging_cfg = load_config("config/logging.yaml")
setup_logging(logging_cfg)

logger = logging.getLogger(__name__)

# Log configuration without exposing secrets
safe_cfg = mask_sensitive_info(config)
logger.info("Loaded configuration: %s", safe_cfg)
```

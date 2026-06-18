import logging.config
import os
import re
from pathlib import Path
from typing import Any

import yaml

SENSITIVE_PATTERNS = {"key", "password", "secret", "token"}

# Pattern matching ${VAR}, ${VAR, default}, ${VAR, "default"}, ${VAR, 'default'}
# Group 1: variable name
# Group 2: quoted default ("..." or '...', quotes preserved for YAML to handle)
# Group 3: unquoted default (} not allowed, backward-compatible)
_PATTERN = re.compile(r"""\$\{([A-Z0-9_]+)(?:,\s*(?:("[^"]*"|'[^']*')|([^}]+?)))?\}""")


def mask_sensitive_info(config: dict[str, Any]) -> dict[str, Any]:
    """Mask sensitive information in the given config dict.

    A key is considered sensitive if its name (case-insensitive) contains any of
    the substrings in ``SENSITIVE_PATTERNS``: ``key``, ``password``, ``secret``,
    or ``token``.  For example, ``api_key``, ``db_password``, ``access_token``,
    and ``client_secret`` are all masked.

    This function is designed for small configuration dicts loaded at startup and
    is not intended for large data sets.

    It processes nested dicts recursively.

    Args:
        config: Configuration dict to mask.

    Returns:
        A new dictionary with sensitive values replaced by ``"***MASKED***"``.

    """
    masked: dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, dict):
            # Recursively mask nested dictionaries
            masked[key] = mask_sensitive_info(value)
        elif any(pat in key.lower() for pat in SENSITIVE_PATTERNS):
            masked[key] = "***MASKED***"
        else:
            masked[key] = value
    return masked


def setup_logging(logging_cfg: dict) -> None:
    """Set up logging configuration from a dict.

    Args:
        logging_cfg: The logging configuration to apply.

    Raises:
        TypeError: If the configuration cannot be converted to a dictionary.

    """
    if not isinstance(logging_cfg, dict):
        msg = (
            f"Logging configuration must be convertible to a dict, but got "
            f"{type(logging_cfg).__name__}."
        )
        raise TypeError(msg)
    logging.config.dictConfig(logging_cfg)


def _replace_env(match: re.Match) -> str:
    """Replace ${VAR} or ${VAR, default} with the appropriate string.

    Internal callback used by re.sub before YAML parsing.

    Rules:
      - If the environment variable VAR exists → substitute its value (raw string)
      - If a quoted default is provided ("..." or '...') → substitute with quotes
        preserved so that YAML handles quoting and type semantics
      - If an unquoted default is provided → substitute it directly (YAML type-casts it)
      - If no default is provided → substitute null

    Args:
        match: The regex match object containing the variable name and optional default.

    Returns:
        The string to substitute in place of the matched pattern.

    """
    var_name = match.group(1)
    default_raw = match.group(2) if match.group(2) is not None else match.group(3)

    # Environment variable exists
    if var_name in os.environ:
        env_val = os.environ[var_name]
        # If the environment variable is an empty string,
        # return it as a quoted string literal to ensure YAML parses it as ""
        if not env_val:
            return '""'
        return env_val

    # No env variable, but a default value was provided
    if default_raw is not None:
        return default_raw

    # No env and no default provided
    return "null"


def _expand_tilde_path_values(value: Any) -> Any:  # noqa: ANN401
    """Recursively expand path-like string values that start with ``~``.

    Args:
        value: Parsed YAML value.

    Returns:
        YAML value with leading-tilde strings expanded when possible.

    """
    if isinstance(value, dict):
        return {
            key: _expand_tilde_path_values(child_value)
            for key, child_value in value.items()
        }

    if isinstance(value, list):
        return [_expand_tilde_path_values(child_value) for child_value in value]

    if isinstance(value, str) and value.startswith("~"):
        expanded_path = Path(value).expanduser()
        expanded = str(expanded_path)
        if expanded.startswith("~"):
            # Keep original when ~user could not be resolved.
            return value
        return expanded

    return value


def load_config(config_path: str) -> dict[str, Any]:
    """Load a YAML configuration file.

    Supported syntax:
        ${VAR}                   → If VAR not set, becomes null
        ${VAR, default}          → If VAR not set, "default" is inserted literally
                                   and then YAML type-casts it.
        ${VAR, "default"}        → Quotes are preserved; YAML treats the value as a
        ${VAR, 'default'}          string, suppressing automatic type casting.
                                   } inside the quoted value is allowed.

    Behavior:
      1. Read the entire YAML file as a raw string.
      2. Perform string-level substitution for ${...} patterns.
      3. Pass the substituted string to PyYAML, allowing YAML to determine types.
            4. Expand leading ``~`` in string values into absolute home paths.

    This design ensures:
      - No custom smart-casting logic is needed.
      - Default values are type-cast by YAML (10→int, false→bool, etc.).
      - Environment variable values are applied before YAML parsing.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Parsed configuration as a Python dict with correct types.

    """
    # Step 1: Load file as raw text
    raw_text = Path(config_path).read_text(encoding="utf-8")

    # Step 2: Replace ${VAR} / ${VAR, default} before YAML parsing
    replaced_text = _PATTERN.sub(_replace_env, raw_text)

    # Step 3: Let YAML parse and type-cast the final text
    parsed_config = yaml.safe_load(replaced_text) or {}

    # Step 4: Expand path-like values that begin with "~"
    return _expand_tilde_path_values(parsed_config)

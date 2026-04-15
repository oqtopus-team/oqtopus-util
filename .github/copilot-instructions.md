# Copilot Instructions for oqtopus-util

## Repository Overview

**oqtopus-util** is a Python library (`oqtopus-util` on PyPI) that provides common utilities and shared functionality for the OQTOPUS quantum computing platform ecosystem. It exposes two main modules:

- **`oqtopus_util.config`** — YAML configuration loading with environment-variable substitution (`${VAR}` / `${VAR, default}`), sensitive-value masking, tilde path expansion, and `logging.config.dictConfig` setup.
- **`oqtopus_util.di`** — A lightweight, configuration-driven dependency injection (DI) container (`DiContainer`) that resolves classes by fully-qualified `_target_` paths, supports singleton/prototype scopes, detects circular dependencies, and resolves `@reference` values. A standalone `load_class` helper is also provided.

## Project Structure

```
src/oqtopus_util/          # Library source (installed package)
  __init__.py
  py.typed                 # PEP 561 marker
  config/
    __init__.py
    config_util.py         # load_config, mask_sensitive_info, setup_logging
  di/
    __init__.py
    di_container.py        # DiContainer, CircularDependencyError
    class_loader.py        # load_class helper

tests/oqtopus_util/        # Mirror of src layout
  config/
    test_config_util.py
  di/
    test_di_container.py

docs/                      # MkDocs documentation source
docs_scripts/              # Helper scripts for doc generation
.github/
  workflows/
    ci.yaml                # Lint → test pipeline
    release.yaml           # Tag-driven PyPI release
    labeler.yaml           # Auto-label PRs by commit prefix
  instructions/            # Copilot formatting guidelines
  pull_request_template.md
```

## Toolchain

| Tool | Purpose | Version pin |
|------|---------|-------------|
| **uv** | Package manager & virtual-env | `.uv-version` → `0.10.9` |
| **Python** | Runtime | `.python-version` → `3.14`; library supports `>=3.11,<4.0` |
| **ruff** | Linter + formatter | `pyproject.toml` `[tool.ruff]` |
| **mypy** | Static type checker | `pyproject.toml` `[tool.mypy]` |
| **pytest** | Test runner with coverage | `pyproject.toml` `[tool.pytest.ini_options]` |
| **pre-commit** | Git hook runner | `.pre-commit-config.yaml` |
| **MkDocs + Material** | Documentation | `mkdocs.yml` |
| **pymarkdownlnt** | Markdown linter for docs | runs on changed `docs/**` files |

## Key Commands

All day-to-day tasks go through `make` (see `Makefile`):

```bash
make install    # uv sync --all-groups + pre-commit install + git commit template
make format     # ruff check --fix && ruff format
make lint       # uv lock --check + ruff check + ruff format --check + mypy
make test       # pytest (with coverage)
make verify     # format + lint + test in sequence
make docs-lint  # pymarkdownlnt scan docs
make docs-build # mkdocs build
make docs-serve # mkdocs serve (local preview)
```

Run `uv` commands directly if you need finer control:

```bash
uv sync --frozen --all-groups   # Install exact locked deps
uv run pytest                   # Run tests
uv run ruff check .             # Lint
uv run mypy src tests           # Type-check
```

## Development Workflow

1. **Branch** off `main` using `feature/xxx`, `bugfix/xxx`, or `hotfix/xxx`.
2. **Commit** with Conventional Commits format: `<type>(<scope>): <summary>` — types: `feat|fix|docs|style|refactor|test|ci|chore`. See `.github/instructions/commit-message.instructions.md`.
3. **Pre-commit hooks** run automatically on `git commit`: `uv-lock --check`, `ruff` (lint + format), `mypy`. Fix any failures before retrying the commit.
4. **CI** (`ci.yaml`) runs on PRs and pushes to `main`:
   - `lint` job: `uv lock --check`, `ruff check`, `ruff format --check`, `mypy`, docs lint (if docs changed).
   - `test` job (needs lint): `pytest --cov=src --cov-report=xml` on Python 3.14; uploads to Codecov.
5. **PR description** should follow `.github/pull_request_template.md` (Ticket / Summary / Changes).

## Code Style & Conventions

- `ruff` is configured with `lint.select = ["ALL"]` with a small ignore list (see `pyproject.toml`). Run `make format` before committing.
- `mypy` checks both `src` and `tests`.
- Tests in `tests/**` have relaxed ruff rules (no `ANN`, `D`, `PLR2004`, `S101`).
- All public functions require docstrings (Google style). Private helpers use `_` prefix.
- The package uses a `src/` layout; `pythonpath = ["src"]` is set for pytest.
- `py.typed` is present — the library is fully typed.

## Adding New Utilities

1. Create a new sub-package under `src/oqtopus_util/<module>/` with `__init__.py`.
2. Export public symbols from `__init__.py`.
3. Mirror the structure under `tests/oqtopus_util/<module>/` with `test_<module>.py`.
4. Add usage docs under `docs/usage/<module>.md` and link from `docs/usage/getting_started.md`.

## Known Errors & Workarounds

- **`uv.lock` out of sync**: pre-commit will abort the commit. Fix with `uv lock` then re-commit.
- **mypy strict mode**: ruff `ANN` rules enforce annotations on all public functions in `src/`; omitting them will cause both ruff and mypy to fail.
- **`exclude-newer = "1 week"`** in `[tool.uv]`: uv pins dependency resolution to packages published within the last week. If a fresh `uv sync` fails to find a package, this setting may be the cause — check `pyproject.toml` and adjust if needed during dependency updates.
- **`actions/checkout@v6`** is used in CI; this is a non-standard version tag (upstream latest is v4). Do not downgrade it without understanding the repository's pinning intent.

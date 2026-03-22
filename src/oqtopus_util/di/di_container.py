import importlib
import threading
from typing import Any


class CircularDependencyError(ValueError):
    """Raised when dependency resolution encounters a reference cycle."""


class DiContainer:
    """A lightweight configuration-based Dependency Injection (DI) container.

    The container receives a fully-parsed configuration dictionary
    (after environment-variable substitution via load_config()) and
    provides objects based on `_target_` class paths.

    Features:
      - Supports `_scope_` = "singleton" (default) or "prototype".
      - `_target_` is required for every component.
            - String values starting with `@` are treated as dependency references.
      - Keys starting with "_" (e.g., `_target_`, `_scope_`) are metadata
        and excluded from constructor arguments.
      - Uses Python's importlib to dynamically import target classes.
      - Singleton instances are cached inside the container.

    Example YAML:

        job_fetcher:
          _target_: oqtopus_engine_core.fetchers.OqtopusCloudJobFetcher
          _scope_: singleton
                    repo: "@job_repo"

                job_repo:
                    _target_: oqtopus_engine_core.repositories.JobRepository
                    base_url: "http://localhost:8888"

    Example usage:

        dicon = DiContainer(registry_config)
        job_fetcher = dicon.get("job_fetcher")

    """

    def __init__(self, registry: dict[str, Any]) -> None:
        """Initialize the DI container.

        Args:
            registry: Configuration dictionary for the dependency registry.
                   Top-level keys represent dependency names.

        """
        self._registry_config = registry
        # Reentrant lock is required because @-references resolve recursively.
        self._lock = threading.RLock()
        # cache for singletons
        self._singleton_instances: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, name: str) -> Any:  # noqa: ANN401
        """Retrieve a dependency by name.

        Behavior:
          - Raise KeyError if the name does not exist in the config.
          - Import the target class defined by `_target_`.
          - Create an instance with kwargs from the component config.
          - Respect `_scope_`:
              - singleton (default): cache the instance
              - prototype: always create a fresh instance

        Args:
            name: Component name to retrieve.

        Returns:
            The created or cached instance.

        Raises:
            KeyError: If the component name is missing.
            ValueError: If `_target_` is missing.
            CircularDependencyError: If dependency references form a cycle.
            ImportError: If module/class cannot be imported.
            TypeError: If constructor arguments mismatch.

        """  # noqa: DOC502
        return self._get(name, resolving=())

    def _get(self, name: str, resolving: tuple[str, ...]) -> Any:  # noqa: ANN401
        """Resolve a dependency with cycle detection context.

        Args:
            name: Component name to retrieve.
            resolving: Tuple of component names currently being resolved for cycle
              detection.

        Returns:
            The created or cached instance.

        Raises:
            KeyError: If the component name is missing.
            CircularDependencyError: If dependency references form a cycle.

        """
        if name in resolving:
            cycle = " -> ".join((*resolving, name))
            message = f"Circular dependency detected: {cycle}"
            raise CircularDependencyError(message)

        if name not in self._registry_config:
            message = f"Unknown dependency: {name}"
            raise KeyError(message)

        next_resolving = (*resolving, name)

        # First check (no lock)
        instance = self._singleton_instances.get(name)
        if instance is not None:
            return instance

        scope = self._registry_config[name].get("_scope_", "singleton")

        # If prototype, no locking needed for cache
        if scope == "prototype":
            return self._create_instance(name, resolving=next_resolving)

        # Double-Checked Locking section
        with self._lock:
            # Second check (after acquiring lock)
            instance = self._singleton_instances.get(name)
            if instance is not None:
                return instance

            # Create and cache
            instance = self._create_instance(name, resolving=next_resolving)
            self._singleton_instances[name] = instance
            return instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_instance(
        self,
        name: str,
        resolving: tuple[str, ...],
    ) -> Any:  # noqa: ANN401
        """Create a new instance for a given component name.

        `_target_` is mandatory. Other keys starting with "_" are ignored.
        All remaining keys are passed to the constructor as kwargs.
        String kwargs starting with `@` are resolved via DiContainer.

        Args:
            name: Component name to create.
            resolving: Tuple of component names currently being resolved for cycle
              detection.

        Returns:
            The created instance.

        Raises:
            ValueError: If `_target_` is missing.
            TypeError: If constructor arguments do not match.

        """
        cfg = self._registry_config[name]

        if "_target_" not in cfg:
            message = f"Missing _target_ for dependency {name}"
            raise ValueError(message)

        klass = self._load_class(cfg["_target_"])

        # Filter out metadata keys (starting with "_")
        kwargs = {
            k: self._resolve_value(v, resolving)
            for k, v in cfg.items()
            if not k.startswith("_")
        }

        # Instantiate with keyword arguments
        try:
            return klass(**kwargs)
        except TypeError as exc:
            message = f"Failed to instantiate {klass.__name__} with arguments {kwargs}"
            raise TypeError(message) from exc

    def _resolve_value(self, value: Any, resolving: tuple[str, ...]) -> Any:  # noqa: ANN401
        """Resolve @-references recursively within config values.

        - If value is a string starting with "@", treat it as a dependency reference.
        - If value is a dict or list, resolve recursively.
        - Otherwise, return the value as-is. This allows for non-string values
          (e.g., integers, booleans) to be used directly.

        Args:
            value: The value to resolve.
            resolving: Tuple of component names currently being resolved for cycle
              detection. This is passed down to resolve nested references.

        Returns:
            The resolved value.

        Raises:
            ValueError: If an @-reference is invalid (e.g., "@", "@ ").

        """
        if isinstance(value, dict):
            return {
                key: self._resolve_value(child_value, resolving)
                for key, child_value in value.items()
            }

        if isinstance(value, list):
            return [
                self._resolve_value(child_value, resolving) for child_value in value
            ]

        if isinstance(value, str) and value.startswith("@"):
            dependency_name = value[1:].strip()
            if not dependency_name:
                message = "Invalid dependency reference: '@'"
                raise ValueError(message)
            return self._get(dependency_name, resolving)

        return value

    @staticmethod
    def _load_class(target: str) -> type:
        """Load a class from a string path.

        Example path: "oqtopus_engine_core.fetchers.OqtopusCloudJobFetcher"

        Args:
            target: Fully-qualified class path.

        Returns:
            The class object.

        Raises:
            ImportError: If module or class cannot be imported.

        """
        try:
            module_path, class_name = target.rsplit(".", 1)
        except ValueError as exc:
            message = f"Invalid _target_ format: {target}"
            raise ImportError(message) from exc

        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            message = f"Cannot import module {module_path}"
            raise ImportError(message) from exc

        try:
            return getattr(module, class_name)
        except AttributeError as exc:
            message = f"Module '{module_path}' has no class {class_name}"
            raise ImportError(message) from exc

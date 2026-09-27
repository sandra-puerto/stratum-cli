"""
Stratum CLI — Database Engine Provider Base Class & Registry
============================================================

Educational Design Pattern: Strategy & Registry Pattern
-------------------------------------------------------
To make `stratum-cli` easily extensible by developers:
1. Each database type (MongoDB, PostgreSQL, Redis, MariaDB, etc.) implements the
   `BaseDatabaseEngine` interface.
2. New engines register themselves using the `@register_engine("engine_name")` decorator.
3. Adding a brand new database (e.g. MariaDB or ClickHouse) requires ONLY creating a new
   file in `stratum_cli/engines/` without modifying core CLI code (Open/Closed Principle - SOLID).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Type


@dataclass
class ProvisioningResult:
    """Standardized result returned after provisioning a tenant database."""
    engine_name: str
    tenant_org: str
    tenant_service: str
    database_name: str
    username: str
    password: str
    boundary_host: str
    boundary_port: int
    connection_uri: str
    env_snippet: str


class BaseDatabaseEngine(ABC):
    """
    Abstract Base Class representing a Stratum Persistence Engine.
    All concrete database drivers must inherit from this class and implement
    its lifecycle methods.
    """

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Human-readable name of the persistence engine (e.g., 'MongoDB')."""
        pass

    @property
    @abstractmethod
    def target_container(self) -> str:
        """Primary Docker container name hosting the engine."""
        pass

    @abstractmethod
    def provision(self, org: str, service: str, password: Optional[str] = None) -> ProvisioningResult:
        """
        Creates an isolated database, dedicated tenant user, and assigns permissions.

        Args:
            org (str): Organization identifier.
            service (str): Service name.
            password (Optional[str]): Explicit password or None to auto-generate.

        Returns:
            ProvisioningResult: Data object containing credentials and connection parameters.
        """
        pass

    @abstractmethod
    def backup(self, org: str, service: str, output_dir: Path) -> Path:
        """
        Executes an isolated, compressed dump of the tenant's database.

        Args:
            org (str): Organization identifier.
            service (str): Service name.
            output_dir (Path): Destination directory for the backup archive.

        Returns:
            Path: Path to the generated backup artifact.
        """
        pass


# Global Engine Registry mapping string identifiers to engine classes
_ENGINE_REGISTRY: Dict[str, Type[BaseDatabaseEngine]] = {}


def register_engine(name: str) -> Callable[[Type[BaseDatabaseEngine]], Type[BaseDatabaseEngine]]:
    """
    Decorator to register a concrete database engine with the global registry.

    Example:
        @register_engine("mongo")
        class MongoEngine(BaseDatabaseEngine):
            ...
    """
    def decorator(cls: Type[BaseDatabaseEngine]) -> Type[BaseDatabaseEngine]:
        _ENGINE_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def get_engine(name: str, root_dir: Optional[Path] = None) -> BaseDatabaseEngine:
    """
    Factory function to retrieve an initialized engine instance by name.

    Args:
        name (str): Engine identifier ('mongo', 'postgres', 'redis', etc.).
        root_dir (Optional[Path]): Stratum-Core root path.

    Returns:
        BaseDatabaseEngine: Concrete engine instance.

    Raises:
        ValueError: If the requested engine is not registered.
    """
    engine_key = name.lower()
    if engine_key not in _ENGINE_REGISTRY:
        available = ", ".join(sorted(_ENGINE_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported database engine: '{name}'. Available engines: {available}"
        )
    return _ENGINE_REGISTRY[engine_key](root_dir=root_dir)


def list_registered_engines() -> Dict[str, Type[BaseDatabaseEngine]]:
    """Returns a copy of all registered engine providers."""
    return dict(_ENGINE_REGISTRY)

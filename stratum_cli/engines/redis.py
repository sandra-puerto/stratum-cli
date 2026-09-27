"""
Stratum CLI — Redis Key-Value Persistence Engine Driver
========================================================

Educational Deep-Dive:
----------------------
In Redis:
1. Stratum-Core configures Redis with AOF (Append-Only File) persistence and password authentication.
2. Applications connect to Redis through the Boundary TCP Proxy at port 6379 over `stratum_dmz`.
"""

from pathlib import Path
from typing import Optional

from ..core.config import find_stratum_root, get_database_env, validate_tenant_identifier
from .base import BaseDatabaseEngine, ProvisioningResult, register_engine


@register_engine("redis")
class RedisEngine(BaseDatabaseEngine):
    """Concrete provider for Redis key-value & cache engine."""

    @property
    def engine_name(self) -> str:
        return "Redis Key-Value & Cache Engine"

    @property
    def target_container(self) -> str:
        return "stratum-database-redis"

    def provision(self, org: str, service: str, password: Optional[str] = None) -> ProvisioningResult:
        db_name = validate_tenant_identifier(org, service)
        root = self.root_dir or find_stratum_root()
        db_env = get_database_env(root)
        redis_pass = password or db_env.get("REDIS_PASSWORD", "")

        host = "stratum-database-nginx"
        port = 6379
        uri = f"redis://:{redis_pass}@{host}:{port}/0"

        env_block = f"""# --- Stratum Boundary Persistence (Redis: {org.upper()}) ---
REDIS_HOST={host}
REDIS_PORT={port}
REDIS_PASSWORD={redis_pass}
REDIS_URL={uri}"""

        return ProvisioningResult(
            engine_name="Redis",
            tenant_org=org,
            tenant_service=service,
            database_name=db_name,
            username="default",
            password=redis_pass,
            boundary_host=host,
            boundary_port=port,
            connection_uri=uri,
            env_snippet=env_block,
        )

    def backup(self, org: str, service: str, output_dir: Path) -> Path:
        raise NotImplementedError("Redis multi-tenant backups are managed via RDB snapshots in stratum-database-redis volume.")

"""
Stratum CLI — PostgreSQL Persistence Engine Driver
===================================================

Educational Deep-Dive:
----------------------
In PostgreSQL:
1. Role Isolation: A PostgreSQL ROLE created with `LOGIN` and assigned as the `OWNER` of a
   specific database has full privileges on that database, but 0 access to peer databases.
2. Custom Format Dumps (`pg_dump -Fc`):
   Using PostgreSQL's custom binary format enables fast gzip compression and allows selective,
   table-level parallel restores (`pg_restore --jobs=4`).
"""

import datetime
import subprocess
from pathlib import Path
from typing import Optional

from ..core.config import (
    find_stratum_root,
    get_database_env,
    generate_secure_password,
    validate_tenant_identifier,
)
from ..core.docker import exec_in_container, is_container_running
from ..core.exceptions import ProvisioningError
from .base import BaseDatabaseEngine, ProvisioningResult, register_engine


@register_engine("postgres")
@register_engine("postgresql")
class PostgresEngine(BaseDatabaseEngine):
    """Concrete provider for PostgreSQL 16+ relational engine."""

    @property
    def engine_name(self) -> str:
        return "PostgreSQL Relational Engine"

    @property
    def target_container(self) -> str:
        return "stratum-database-postgres"

    def provision(self, org: str, service: str, password: Optional[str] = None) -> ProvisioningResult:
        db_name = validate_tenant_identifier(org, service)
        user_name = org.lower()
        app_password = password or generate_secure_password(24)

        if not is_container_running(self.target_container):
            raise ProvisioningError(
                f"Container '{self.target_container}' is not running. "
                "Deploy stratum-core/database before provisioning tenants."
            )

        root = self.root_dir or find_stratum_root()
        db_env = get_database_env(root)
        admin_user = db_env.get("POSTGRES_USER", "stratum_admin")
        admin_db = db_env.get("POSTGRES_DB", "stratum_db")

        # 1. Create Role Idempotently
        role_sql = f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{user_name}') THEN
                CREATE ROLE {user_name} WITH LOGIN PASSWORD '{app_password}';
            ELSE
                ALTER ROLE {user_name} WITH PASSWORD '{app_password}';
            END IF;
        END
        $$;
        """
        code, out, err = exec_in_container(self.target_container, ["psql", "-U", admin_user, "-d", admin_db, "-c", role_sql])
        if code != 0:
            raise ProvisioningError(f"Failed to create PostgreSQL role '{user_name}':\n{err}")

        # 2. Create Database with Owner
        create_db_sql = f"CREATE DATABASE {db_name} OWNER {user_name};"
        code_db, _, err_db = exec_in_container(self.target_container, ["psql", "-U", admin_user, "-d", admin_db, "-c", create_db_sql])
        if code_db != 0 and "already exists" not in err_db.lower():
            raise ProvisioningError(f"Failed to create PostgreSQL database '{db_name}':\n{err_db}")

        # 3. Grant Privileges
        grant_sql = f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {user_name};"
        exec_in_container(self.target_container, ["psql", "-U", admin_user, "-d", admin_db, "-c", grant_sql])

        host = "stratum-database-nginx"
        port = 5432
        uri = f"postgresql://{user_name}:{app_password}@{host}:{port}/{db_name}"

        env_block = f"""# --- Stratum Boundary Persistence (Tenant: {org.upper()}) ---
STRATUM_DB_HOST={host}
DB_USER={user_name}
DB_PASSWORD={app_password}
DB_NAME={db_name}
DATABASE_URL={uri}"""

        return ProvisioningResult(
            engine_name="PostgreSQL",
            tenant_org=org,
            tenant_service=service,
            database_name=db_name,
            username=user_name,
            password=app_password,
            boundary_host=host,
            boundary_port=port,
            connection_uri=uri,
            env_snippet=env_block,
        )

    def backup(self, org: str, service: str, output_dir: Path) -> Path:
        db_name = validate_tenant_identifier(org, service)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        tenant_dir = output_dir / org.lower()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        backup_file = tenant_dir / f"{db_name}_{timestamp}.pgdump"

        root = self.root_dir or find_stratum_root()
        db_env = get_database_env(root)
        admin_user = db_env.get("POSTGRES_USER", "stratum_admin")

        cmd = ["docker", "exec", self.target_container, "pg_dump", "-U", admin_user, "-Fc", db_name]

        with open(backup_file, "wb") as f:
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=False)

        if res.returncode != 0:
            if backup_file.exists():
                backup_file.unlink()
            raise ProvisioningError(f"PostgreSQL backup failed:\n{res.stderr.decode('utf-8', errors='ignore')}")

        return backup_file

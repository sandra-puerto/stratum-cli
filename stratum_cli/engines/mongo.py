"""
Stratum CLI — MongoDB Persistence Engine Driver
================================================

Educational Deep-Dive:
----------------------
In MongoDB:
1. Security Scoping: A tenant user created within database `sgpt_overleaf` with role `readWrite`
   CANNOT inspect, list, or query collections in other databases (e.g. `isora_portal`).
2. Authentication Database: By setting `authSource=<tenant_db>`, each tenant authenticates
   strictly against their own database namespace rather than the shared `admin` database.
3. Streaming Backups: Using `mongodump --archive --gzip` pipes the compressed binary stream
   directly over Docker stdout to the host filesystem, preventing disk fill-up inside the container.
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


@register_engine("mongo")
@register_engine("mongodb")
class MongoEngine(BaseDatabaseEngine):
    """Concrete provider for MongoDB 7.x / 8.x document store."""

    @property
    def engine_name(self) -> str:
        return "MongoDB Document Engine"

    @property
    def target_container(self) -> str:
        return "stratum-database-mongodb"

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
        root_user = db_env.get("MONGO_ROOT_USERNAME", "stratum_admin")
        root_pass = db_env.get("MONGO_ROOT_PASSWORD", "")

        # JavaScript snippet evaluated securely via mongosh inside the container
        js_payload = f"""
        db = db.getSiblingDB('{db_name}');
        try {{
            db.createUser({{
                user: '{user_name}',
                pwd: '{app_password}',
                roles: [
                    {{ role: 'readWrite', db: '{db_name}' }},
                    {{ role: 'dbAdmin', db: '{db_name}' }}
                ]
            }});
            print('SUCCESS_USER_CREATED');
        }} catch (e) {{
            if (e.message && e.message.includes('already exists')) {{
                db.changeUserPassword('{user_name}', '{app_password}');
                print('SUCCESS_PASSWORD_UPDATED');
            }} else {{
                print('ERROR: ' + e);
            }}
        }}
        """

        cmd = ["mongosh", "--quiet"]
        if root_pass:
            cmd.extend(["-u", root_user, "-p", root_pass, "--authenticationDatabase", "admin"])
        cmd.extend(["--eval", js_payload])

        code, out, err = exec_in_container(self.target_container, cmd)
        if code != 0 or "ERROR:" in out:
            raise ProvisioningError(
                f"MongoDB tenant provisioning failed:\nStdout: {out}\nStderr: {err}"
            )

        host = "stratum-database-nginx"
        port = 27017
        uri = f"mongodb://{user_name}:{app_password}@{host}:{port}/{db_name}?authSource={db_name}"

        env_block = f"""# --- Stratum Boundary Persistence (Tenant: {org.upper()}) ---
STRATUM_DB_HOST={host}
MONGO_APP_USER={user_name}
MONGO_APP_PASSWORD={app_password}
MONGO_DB_NAME={db_name}
MONGO_AUTH_SOURCE={db_name}
MONGO_URL={uri}"""

        return ProvisioningResult(
            engine_name="MongoDB",
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
        backup_file = tenant_dir / f"{db_name}_{timestamp}.archive.gz"

        root = self.root_dir or find_stratum_root()
        db_env = get_database_env(root)
        root_user = db_env.get("MONGO_ROOT_USERNAME", "stratum_admin")
        root_pass = db_env.get("MONGO_ROOT_PASSWORD", "")

        cmd = ["docker", "exec", self.target_container, "mongodump"]
        if root_pass:
            cmd.extend(["-u", root_user, "-p", root_pass, "--authenticationDatabase", "admin"])
        cmd.extend(["--db", db_name, "--gzip", "--archive"])

        with open(backup_file, "wb") as f:
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=False)

        if res.returncode != 0:
            if backup_file.exists():
                backup_file.unlink()
            raise ProvisioningError(f"MongoDB backup failed:\n{res.stderr.decode('utf-8', errors='ignore')}")

        return backup_file

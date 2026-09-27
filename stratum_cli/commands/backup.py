"""
Stratum CLI — Backup Command Controller
=======================================
Orchestrates isolated tenant backups via the respective database engine provider.
"""

import sys
from pathlib import Path
from ..engines import get_engine
from ..core.exceptions import StratumError


def backup_tenant_db(org: str, service: str, engine: str, output_dir: str = "/opt/backups"):
    """
    Executes an isolated tenant database backup.

    Args:
        org (str): Organization identifier.
        service (str): Service name.
        engine (str): Engine type ('mongo', 'postgres').
        output_dir (str): Base backup directory.
    """
    try:
        dest_path = Path(output_dir)
        driver = get_engine(engine)
        backup_file = driver.backup(org=org, service=service, output_dir=dest_path)

        size_kb = backup_file.stat().st_size / 1024.0
        print("=" * 80)
        print(f"[+] STRATUM TENANT BACKUP COMPLETED ({driver.engine_name})")
        print("=" * 80)
        print(f"  Organization ....... : {org.upper()}")
        print(f"  Service ............ : {service}")
        print(f"  Artifact ........... : {backup_file}")
        print(f"  Archive Size ....... : {size_kb:.2f} KB")
        print("=" * 80)

    except StratumError as err:
        print(f"[-] Backup Error: {err.message}", file=sys.stderr)
        sys.exit(err.exit_code)
    except Exception as exc:
        print(f"[-] Unexpected Error during backup: {exc}", file=sys.stderr)
        sys.exit(1)

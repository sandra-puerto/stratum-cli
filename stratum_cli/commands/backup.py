"""
Stratum CLI — Backup Command Controller
=======================================
"""

import sys
from pathlib import Path
from ..engines import get_engine
from ..core.exceptions import StratumError
from ..core.i18n import t


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
        print(t("bk_success_title", engine=driver.engine_name))
        print("=" * 80)
        print(f"  Organization ....... : {org.upper()}")
        print(f"  Service ............ : {service}")
        print(t("bk_artifact", file=backup_file))
        print(t("bk_size", size=f"{size_kb:.2f}"))
        print("=" * 80)

    except StratumError as err:
        print(t("bk_error", err=err.message), file=sys.stderr)
        sys.exit(err.exit_code)
    except Exception as exc:
        print(f"[-] Unexpected Error: {exc}", file=sys.stderr)
        sys.exit(1)

"""
Stratum CLI — Database Command Controller
=========================================
"""

import sys
from typing import Optional
from ..engines import get_engine, list_registered_engines
from ..core.exceptions import StratumError
from ..core.i18n import t


def create_tenant_db(org: str, service: str, engine: str, password: Optional[str] = None):
    """
    Orchestrates the creation of a tenant database using the appropriate engine provider.

    Args:
        org (str): Organization name (e.g. 'sgpt').
        service (str): Service name (e.g. 'overleaf').
        engine (str): Persistence engine type ('mongo', 'postgres', 'redis').
        password (Optional[str]): Optional custom password.
    """
    try:
        driver = get_engine(engine)
        res = driver.provision(org=org, service=service, password=password)

        print("=" * 80)
        print(t("prov_success_title", engine=res.engine_name))
        print("=" * 80)
        print(t("prov_org", org=res.tenant_org.upper()))
        print(t("prov_service", service=res.tenant_service))
        print(t("prov_db", db=res.database_name))
        print(t("prov_user", user=res.username))
        print(t("prov_password", password=res.password))
        print(t("prov_proxy", host=res.boundary_host, port=res.boundary_port))
        print("-" * 80)
        print(t("prov_uri_header"))
        print(f"  {res.connection_uri}")
        print("-" * 80)
        print(t("prov_env_header"))
        print(f"\n{res.env_snippet}\n")
        print("=" * 80)

    except StratumError as err:
        print(f"[-] Error: {err.message}", file=sys.stderr)
        sys.exit(err.exit_code)
    except Exception as exc:
        print(f"[-] Unexpected Error: {exc}", file=sys.stderr)
        sys.exit(1)


def list_engines():
    """Prints all registered database engines available in the platform."""
    engines = list_registered_engines()
    print("Available Stratum persistence engines:")
    for name, cls in engines.items():
        print(f"  - {name:<12} ({cls.__name__})")

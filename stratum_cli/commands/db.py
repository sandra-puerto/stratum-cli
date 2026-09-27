"""
Stratum CLI — Database Command Controller
=========================================

Educational Design Note:
------------------------
This controller acts as the orchestrator between the CLI input layer and the
database engine strategy providers (`stratum_cli.engines.*`).
"""

import sys
from typing import Optional
from ..engines import get_engine, list_registered_engines
from ..core.exceptions import StratumError


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
        print(f"[+] STRATUM MULTI-TENANT PROVISIONING SUCCESSFUL ({res.engine_name})")
        print("=" * 80)
        print(f"  Organization ....... : {res.tenant_org.upper()}")
        print(f"  Service ............ : {res.tenant_service}")
        print(f"  Tenant Database .... : {res.database_name}")
        print(f"  Application User ... : {res.username}")
        print(f"  Generated Password . : {res.password}")
        print(f"  Boundary Proxy ..... : {res.boundary_host}:{res.boundary_port}")
        print("-" * 80)
        print("  Connection URI:")
        print(f"  {res.connection_uri}")
        print("-" * 80)
        print("  Copy-Paste for Tenant .env file:")
        print(f"\n{res.env_snippet}\n")
        print("=" * 80)

    except StratumError as err:
        print(f"[-] Provisioning Error: {err.message}", file=sys.stderr)
        sys.exit(err.exit_code)
    except Exception as exc:
        print(f"[-] Unexpected Error during provisioning: {exc}", file=sys.stderr)
        sys.exit(1)


def list_engines():
    """Prints all registered database engines available in the platform."""
    engines = list_registered_engines()
    print("Available Stratum persistence engines:")
    for name, cls in engines.items():
        print(f"  - {name:<12} ({cls.__name__})")

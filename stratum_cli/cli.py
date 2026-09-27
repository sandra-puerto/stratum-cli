"""
Stratum CLI — Main Application Dispatcher & CLI Router
======================================================

Educational Overview:
---------------------
This module uses Python's standard `argparse` module to implement a hierarchical,
subcommand-driven CLI interface (similar to `docker` or `kubectl`).

By keeping dependencies within the Python standard library, `stratum-cli` installs and
executes instantly on any Linux server, container, or CI/CD runner with zero virtual
environment bootstrapping required.
"""

import argparse
import sys
from . import __version__
from .commands.db import create_tenant_db, list_engines
from .commands.gateway import add_tenant_tunnel
from .commands.backup import backup_tenant_db
from .commands.status import show_platform_status
from .commands.doctor import run_diagnostics


def build_parser() -> argparse.ArgumentParser:
    """Constructs the complete CLI argument parser hierarchy."""
    parser = argparse.ArgumentParser(
        prog="stratum",
        description="Stratum CLI — Autonomous Multi-Tenant Persistence & Lifecycle Orchestrator",
        epilog="Engineered by Sandra Gabriela Puerto Torres — https://sandrapuerto.com"
    )
    parser.add_argument("-v", "--version", action="version", version=f"Stratum CLI v{__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available Stratum commands")

    # =========================================================================
    # 1. DATABASE COMMANDS ('stratum db ...')
    # =========================================================================
    db_parser = subparsers.add_parser("db", help="Database & multi-tenant persistence provisioning")
    db_sub = db_parser.add_subparsers(dest="db_command")

    # stratum db create <org> <service> [-e mongo|postgres|redis] [-p password]
    create_parser = db_sub.add_parser("create", help="Create an isolated tenant database & dedicated user")
    create_parser.add_argument("org", help="Organization identifier (e.g., 'sgpt', 'isora')")
    create_parser.add_argument("service", help="Service name (e.g., 'overleaf', 'nextcloud')")
    create_parser.add_argument(
        "-e", "--engine",
        default="mongo",
        choices=["mongo", "mongodb", "postgres", "postgresql", "redis"],
        help="Persistence engine (default: mongo)"
    )
    create_parser.add_argument(
        "-p", "--password",
        help="Custom password (optional; generates a 24-char cryptographic password if omitted)"
    )

    # stratum db list-engines
    db_sub.add_parser("list-engines", help="List all registered persistence engine providers")

    # =========================================================================
    # 2. GATEWAY COMMANDS ('stratum gateway ...')
    # =========================================================================
    gw_parser = subparsers.add_parser("gateway", help="Gateway & Cloudflare Zero Trust tunnel management")
    gw_sub = gw_parser.add_subparsers(dest="gw_command")

    # stratum gateway add <org> --token <token>
    gw_add = gw_sub.add_parser("add", help="Register a tenant Cloudflare tunnel in gateway/.env")
    gw_add.add_argument("org", help="Organization identifier (e.g., 'SGPT', 'ISORA')")
    gw_add.add_argument("-t", "--token", required=True, help="Cloudflare Tunnel token from Zero Trust dashboard")

    # =========================================================================
    # 3. BACKUP COMMANDS ('stratum backup ...')
    # =========================================================================
    bk_parser = subparsers.add_parser("backup", help="Isolated tenant database backup & dump")
    bk_parser.add_argument("org", help="Organization name (e.g., 'sgpt')")
    bk_parser.add_argument("service", help="Service name (e.g., 'overleaf')")
    bk_parser.add_argument(
        "-e", "--engine",
        default="mongo",
        choices=["mongo", "mongodb", "postgres", "postgresql"],
        help="Database engine type"
    )
    bk_parser.add_argument(
        "-o", "--output-dir",
        default="/opt/backups",
        help="Target backup directory (default: /opt/backups)"
    )

    # =========================================================================
    # 4. STATUS & DIAGNOSTICS ('stratum status', 'stratum doctor')
    # =========================================================================
    subparsers.add_parser("status", help="Inspect platform health and running container topology")
    subparsers.add_parser("doctor", help="Run system diagnostics, kernel check, and security audit")

    return parser


def main():
    """Main CLI execution router."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "db":
        if args.db_command == "create":
            create_tenant_db(args.org, args.service, args.engine, args.password)
        elif args.db_command == "list-engines":
            list_engines()
        else:
            parser.parse_args(["db", "--help"])
    elif args.command == "gateway":
        if args.gw_command == "add":
            add_tenant_tunnel(args.org, args.token)
        else:
            parser.parse_args(["gateway", "--help"])
    elif args.command == "backup":
        backup_tenant_db(args.org, args.service, args.engine, args.output_dir)
    elif args.command == "status":
        show_platform_status()
    elif args.command == "doctor":
        run_diagnostics()


if __name__ == "__main__":
    main()

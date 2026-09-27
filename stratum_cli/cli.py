"""
Stratum CLI — Main Application Dispatcher & CLI Router (i18n-Enabled)
======================================================================
"""

import argparse
import sys
from . import __version__
from .commands.db import create_tenant_db, list_engines
from .commands.gateway import add_tenant_tunnel
from .commands.backup import backup_tenant_db
from .commands.status import show_platform_status
from .commands.doctor import run_diagnostics
from .core.i18n import t, set_language, get_language


def build_parser() -> argparse.ArgumentParser:
    """Constructs the complete CLI argument parser hierarchy with i18n support."""
    parser = argparse.ArgumentParser(
        prog="stratum",
        description=t("cli_desc"),
        epilog=t("cli_epilog")
    )
    parser.add_argument("-v", "--version", action="version", version=f"Stratum CLI v{__version__}")
    parser.add_argument(
        "-l", "--lang",
        choices=["en", "es"],
        default=get_language(),
        help=t("lang_help")
    )

    subparsers = parser.add_subparsers(dest="command", help="Available Stratum commands")

    # =========================================================================
    # 1. DATABASE COMMANDS ('stratum db ...')
    # =========================================================================
    db_parser = subparsers.add_parser("db", help=t("cmd_db"))
    db_sub = db_parser.add_subparsers(dest="db_command")

    # stratum db create <org> <service> [-e mongo|postgres|redis] [-p password]
    create_parser = db_sub.add_parser("create", help=t("cmd_db_create"))
    create_parser.add_argument("org", help=t("arg_org"))
    create_parser.add_argument("service", help=t("arg_service"))
    create_parser.add_argument(
        "-e", "--engine",
        default="mongo",
        choices=["mongo", "mongodb", "postgres", "postgresql", "redis"],
        help=t("arg_engine")
    )
    create_parser.add_argument("-p", "--password", help=t("arg_password"))

    # stratum db list-engines
    db_sub.add_parser("list-engines", help=t("cmd_db_list"))

    # =========================================================================
    # 2. GATEWAY COMMANDS ('stratum gateway ...')
    # =========================================================================
    gw_parser = subparsers.add_parser("gateway", help=t("cmd_gw"))
    gw_sub = gw_parser.add_subparsers(dest="gw_command")

    # stratum gateway add <org> --token <token>
    gw_add = gw_sub.add_parser("add", help=t("cmd_gw_add"))
    gw_add.add_argument("org", help=t("arg_org"))
    gw_add.add_argument("-t", "--token", required=True, help=t("arg_token"))

    # =========================================================================
    # 3. BACKUP COMMANDS ('stratum backup ...')
    # =========================================================================
    bk_parser = subparsers.add_parser("backup", help=t("cmd_bk"))
    bk_parser.add_argument("org", help=t("arg_org"))
    bk_parser.add_argument("service", help=t("arg_service"))
    bk_parser.add_argument(
        "-e", "--engine",
        default="mongo",
        choices=["mongo", "mongodb", "postgres", "postgresql"],
        help=t("arg_engine")
    )
    bk_parser.add_argument("-o", "--output-dir", default="/opt/backups", help=t("arg_output_dir"))

    # =========================================================================
    # 4. STATUS & DIAGNOSTICS ('stratum status', 'stratum doctor')
    # =========================================================================
    subparsers.add_parser("status", help=t("cmd_status"))
    subparsers.add_parser("doctor", help=t("cmd_doctor"))

    return parser


def main():
    """Main CLI execution router with dynamic language switching."""
    # Pre-parse --lang flag if passed early
    for idx, arg in enumerate(sys.argv[:-1]):
        if arg in ("--lang", "-l"):
            set_language(sys.argv[idx + 1])

    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "lang", None):
        set_language(args.lang)

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

"""
Stratum CLI — Platform Health & Status Inspector
================================================
"""

from ..core.docker import is_docker_available, get_container_health
from ..core.i18n import t


CORE_CONTAINERS = [
    ("DMZ Anchor", "stratum-dmz-anchor"),
    ("Gateway NPM Proxy", "stratum-gateway-npm"),
    ("Gateway Primary Tunnel", "stratum-gateway-cloudflared-ICG"),
    ("Gateway Secondary Tunnel", "stratum-gateway-cloudflared-SGPT"),
    ("Database PostgreSQL", "stratum-database-postgres"),
    ("Database MongoDB", "stratum-database-mongodb"),
    ("Database Redis", "stratum-database-redis"),
    ("Database TCP Proxy", "stratum-database-nginx"),
]


def show_platform_status():
    """Inspect and report the runtime status of all Stratum-Core components."""
    if not is_docker_available():
        print("[-] Error: Docker daemon is not available or not running.")
        return

    print("=" * 80)
    print(t("status_title"))
    print("=" * 80)
    print(f"{t('status_col_role'):<30} | {t('status_col_container'):<34} | {t('status_col_health'):<12}")
    print("-" * 80)

    for role, container in CORE_CONTAINERS:
        health = get_container_health(container)
        status_icon = "[+]" if health in ("healthy", "running") else "[-]"
        print(f"{role:<30} | {container:<34} | {status_icon} {health:<8}")

    print("=" * 80)

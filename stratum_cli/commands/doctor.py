"""
Stratum CLI — Platform Doctor & Diagnostics
===========================================
"""

import os
import subprocess
from pathlib import Path
from ..core.config import find_stratum_root
from ..core.docker import is_docker_available
from ..core.i18n import t


def run_diagnostics():
    """Runs a complete diagnostic check of host system, kernel, and Docker platform."""
    print("=" * 80)
    print(t("doc_title"))
    print("=" * 80)

    checks_passed = 0
    total_checks = 0

    # 1. Docker Daemon Check
    total_checks += 1
    if is_docker_available():
        print(f"{t('doc_pass')} {t('doc_docker_ok')}")
        checks_passed += 1
    else:
        print(f"{t('doc_fail')} {t('doc_docker_fail')}")

    # 2. Stratum Core Root Directory Check
    total_checks += 1
    root = find_stratum_root()
    if root.exists() and (root / "dmz").exists() and (root / "database").exists():
        print(f"{t('doc_pass')} {t('doc_root_ok', root=root)}")
        checks_passed += 1
    else:
        print(f"{t('doc_warn')} {t('doc_root_warn')}")

    # 3. Stratum DMZ Network Check
    total_checks += 1
    try:
        res = subprocess.run(
            ["docker", "network", "inspect", "stratum_dmz"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        if res.returncode == 0:
            print(f"{t('doc_pass')} {t('doc_dmz_ok')}")
            checks_passed += 1
        else:
            print(f"{t('doc_warn')} {t('doc_dmz_warn')}")
    except Exception:
        print(f"{t('doc_fail')} {t('doc_dmz_fail')}")

    # 4. Kernel Memory Overcommit Check (Redis recommendation)
    total_checks += 1
    overcommit_path = Path("/proc/sys/vm/overcommit_memory")
    if overcommit_path.exists():
        val = overcommit_path.read_text().strip()
        if val == "1":
            print(f"{t('doc_pass')} {t('doc_overcommit_ok')}")
            checks_passed += 1
        else:
            print(f"{t('doc_warn')} {t('doc_overcommit_warn', val=val)}")
    else:
        print(f"{t('doc_info')} {t('doc_overcommit_skip')}")
        checks_passed += 1

    # 5. File Permission Security Audit on .env files
    total_checks += 1
    env_leak = False
    for comp in ["dmz", "gateway", "database"]:
        env_file = root / comp / ".env"
        if env_file.exists():
            st_mode = oct(env_file.stat().st_mode & 0o777)
            if os.name != "nt" and st_mode not in ("0o600", "0o400"):
                print(f"{t('doc_warn')} {t('doc_perm_warn', file=env_file, mode=st_mode)}")
                env_leak = True

    if not env_leak:
        print(f"{t('doc_pass')} {t('doc_perm_ok')}")
        checks_passed += 1

    print("-" * 80)
    print(t("doc_summary", passed=checks_passed, total=total_checks))
    print("=" * 80)

"""
Stratum CLI — Platform Doctor & Diagnostics
===========================================

Educational Purpose:
--------------------
`stratum doctor` is a diagnostic suite inspired by `brew doctor` and `flutter doctor`.
It helps junior engineers and platform operators quickly pinpoint infrastructure
misconfigurations (kernel limits, memory pressure, missing networks, file permission leaks).
"""

import os
import shutil
import subprocess
from pathlib import Path
from ..core.config import find_stratum_root
from ..core.docker import is_docker_available, get_container_health


def run_diagnostics():
    """Runs a complete diagnostic check of host system, kernel, and Docker platform."""
    print("=" * 80)
    print(" STRATUM PLATFORM DIAGNOSTICS & SYSTEM DOCTOR")
    print("=" * 80)

    checks_passed = 0
    total_checks = 0

    # 1. Docker Daemon Check
    total_checks += 1
    if is_docker_available():
        print("[PASS] 1. Docker Daemon: Responsive and accessible.")
        checks_passed += 1
    else:
        print("[FAIL] 1. Docker Daemon: Not running or current user lacks docker group privileges.")

    # 2. Stratum Core Root Directory Check
    total_checks += 1
    root = find_stratum_root()
    if root.exists() and (root / "dmz").exists() and (root / "database").exists():
        print(f"[PASS] 2. Stratum Core Root: Located at '{root}'.")
        checks_passed += 1
    else:
        print(f"[WARN] 2. Stratum Core Root: Not found at standard locations (/opt/stratum-core).")

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
            print("[PASS] 3. Shared DMZ Network: 'stratum_dmz' is active.")
            checks_passed += 1
        else:
            print("[WARN] 3. Shared DMZ Network: 'stratum_dmz' not found. Run 'docker compose up -d' in dmz/.")
    except Exception:
        print("[FAIL] 3. Shared DMZ Network: Unable to inspect docker networks.")

    # 4. Kernel Memory Overcommit Check (Redis recommendation)
    total_checks += 1
    overcommit_path = Path("/proc/sys/vm/overcommit_memory")
    if overcommit_path.exists():
        val = overcommit_path.read_text().strip()
        if val == "1":
            print("[PASS] 4. Kernel Overcommit: vm.overcommit_memory is tuned to '1'.")
            checks_passed += 1
        else:
            print(f"[WARN] 4. Kernel Overcommit: vm.overcommit_memory is '{val}' (recommended: '1' for Redis).")
    else:
        print("[INFO] 4. Kernel Overcommit: Not a Linux host (skipping /proc check).")
        checks_passed += 1

    # 5. File Permission Security Audit on .env files
    total_checks += 1
    env_leak = False
    for comp in ["dmz", "gateway", "database"]:
        env_file = root / comp / ".env"
        if env_file.exists():
            st_mode = oct(env_file.stat().st_mode & 0o777)
            # On Linux, 0o600 or 0o400 is ideal
            if os.name != "nt" and st_mode not in ("0o600", "0o400"):
                print(f"[WARN] 5. Permissions: '{env_file}' has permissions {st_mode} (recommended: chmod 600).")
                env_leak = True

    if not env_leak:
        print("[PASS] 5. File Permissions: Secret .env files are secure.")
        checks_passed += 1

    print("-" * 80)
    print(f" Diagnostic Summary: {checks_passed}/{total_checks} checks passed.")
    print("=" * 80)

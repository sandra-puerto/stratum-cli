#!/usr/bin/env bash
# ============================================================================
# STRATUM-CLI — Standalone System Installer
# Installation target: /usr/local/bin/stratum
# ============================================================================

set -euo pipefail

INSTALL_DIR="/usr/local/bin"
TARGET="${INSTALL_DIR}/stratum"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "===================================================================="
echo " Installing Stratum-CLI orchestrator..."
echo "===================================================================="

# Check Python 3 presence
if ! command -v python3 &>/dev/null; then
    echo "[-] Error: python3 is required but not installed." >&2
    exit 1
fi

# Create global executable wrapper
sudo tee "${TARGET}" > /dev/null <<EOF
#!/usr/bin/env bash
PYTHONPATH="${REPO_DIR}:\${PYTHONPATH:-}" exec python3 -m stratum_cli.cli "\$@"
EOF

sudo chmod +x "${TARGET}"

echo "[+] Stratum-CLI successfully installed to ${TARGET}!"
echo "--------------------------------------------------------------------"
echo " Verify installation:"
echo "   $ stratum --help"
echo "   $ stratum status"
echo "===================================================================="

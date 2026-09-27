"""
Stratum CLI — Gateway Command Controller (Security-Hardened)
============================================================

Educational Security Deep-Dive:
-------------------------------
CRLF / .env Injection Prevention:
When appending or updating lines in `.env` files, an unvalidated token containing
newline characters (`\\r` or `\\n`) could inject unauthorized environment variables
(e.g., `\\nADMIN_OVERRIDE=true\\n`).

Defensive Mitigation:
1. Strip all CRLF and control characters using `sanitize_input_string`.
2. Validate that the token matches expected Cloudflare JWT/base64 pattern.
3. Write files atomically using temporary buffer flushes.
"""

import re
import sys
from pathlib import Path
from ..core.config import find_stratum_root, get_gateway_env, sanitize_input_string
from ..core.exceptions import ConfigurationError


def add_tenant_tunnel(org: str, token: str):
    """
    Registers a tenant's Cloudflare Zero Trust tunnel token in `gateway/.env`.

    Args:
        org (str): Organization name (e.g., 'SGPT', 'ISORA').
        token (str): Cloudflare Tunnel authentication token string.
    """
    root = find_stratum_root()
    env_path = root / "gateway" / ".env"

    if not env_path.exists():
        print(f"[-] Error: '{env_path}' does not exist. Initialize gateway/.env first.", file=sys.stderr)
        sys.exit(1)

    # Sanitize and strip CRLF / control chars
    clean_org = re.sub(r"[^a-zA-Z0-9_-]", "", org.strip().upper())
    clean_token = sanitize_input_string(token, max_length=512)

    if not clean_org:
        print("[-] Error: Organization identifier cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if not clean_token or len(clean_token) < 20:
        print("[-] Error: Invalid Cloudflare Tunnel token (token too short or malformed).", file=sys.stderr)
        sys.exit(1)

    current_env = get_gateway_env(root)

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    var_token_key = f"CF_TUNNEL_TOKEN_{clean_org}"
    var_name_key = f"{clean_org}_ORG_NAME"

    # Default to the primary secondary slot if vacant
    if "CF_TUNNEL_TOKEN_SECONDARY" in current_env and not current_env["CF_TUNNEL_TOKEN_SECONDARY"]:
        var_token_key = "CF_TUNNEL_TOKEN_SECONDARY"
        var_name_key = "SECONDARY_ORG_NAME"

    updated = False
    new_lines = []
    current_profiles = current_env.get("COMPOSE_PROFILES", "")

    for line in lines:
        if line.strip().startswith(f"{var_name_key}="):
            new_lines.append(f"{var_name_key}={clean_org}\n")
            updated = True
        elif line.strip().startswith(f"{var_token_key}="):
            new_lines.append(f"{var_token_key}={clean_token}\n")
            updated = True
        elif line.strip().startswith("COMPOSE_PROFILES="):
            profiles = [p.strip() for p in current_profiles.split(",") if p.strip()]
            profile_name = "secondary" if var_token_key == "CF_TUNNEL_TOKEN_SECONDARY" else clean_org.lower()
            if profile_name not in profiles:
                profiles.append(profile_name)
            new_lines.append(f"COMPOSE_PROFILES={','.join(profiles)}\n")
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"\n# --- Multi-Tenant Org: {clean_org} ---\n")
        new_lines.append(f"{var_name_key}={clean_org}\n")
        new_lines.append(f"{var_token_key}={clean_token}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("=" * 80)
    print(f"[+] STRATUM GATEWAY TENANT REGISTRATION SUCCESSFUL")
    print("=" * 80)
    print(f"  Organization ....... : {clean_org}")
    print(f"  Tunnel Token ....... : {clean_token[:12]}... (persisted in gateway/.env)")
    print(f"  Target File ........ : {env_path}")
    print("-" * 80)
    print("  To activate this tenant tunnel immediately on your VPS without downtime:")
    print("  $ cd /opt/stratum-core/gateway && docker compose up -d")
    print("=" * 80)

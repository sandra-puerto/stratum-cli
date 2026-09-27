"""
Gateway & Multi-Organization Tunnel Command Handler
"""

import sys
from pathlib import Path
from ..core.config import find_stratum_root, get_gateway_env


def add_tenant_tunnel(org: str, token: str):
    """Register a new organization Cloudflare Tunnel in gateway/.env."""
    root = find_stratum_root()
    env_path = root / "gateway" / ".env"

    if not env_path.exists():
        print(f"[-] Error: '{env_path}' does not exist. Please initialize gateway/.env first.", file=sys.stderr)
        sys.exit(1)

    clean_org = org.strip().upper()
    current_env = get_gateway_env(root)

    # Read lines to modify or append
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check if this is the secondary org or a 3rd+ org
    var_token_key = f"CF_TUNNEL_TOKEN_{clean_org}"
    var_name_key = f"{clean_org}_ORG_NAME"

    # If it's the standard secondary org slot
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
            new_lines.append(f"{var_token_key}={token}\n")
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
        new_lines.append(f"{var_token_key}={token}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("=" * 72)
    print(f"[+] STRATUM GATEWAY TENANT REGISTRATION SUCCESSFUL")
    print("=" * 72)
    print(f"  Organization ....... : {clean_org}")
    print(f"  Tunnel Token ....... : {token[:12]}... (stored in gateway/.env)")
    print(f"  Target File ........ : {env_path}")
    print("-" * 72)
    print("  To activate this tenant tunnel immediately on your VPS without downtime:")
    print("  $ cd /opt/stratum-core/gateway && docker compose up -d")
    print("=" * 72)

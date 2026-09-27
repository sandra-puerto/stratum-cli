"""
Stratum CLI — Core Configuration & Tenant Validation (Security-Hardened)
========================================================================

Educational Security Architecture:
----------------------------------
In multi-tenant platforms, input validation is the primary line of defense against:
1. SQL & NoSQL Injection: Restricting identifiers to a strict, safe character set
   (`^[a-z0-9_]+$`) ensures names cannot carry SQL/JS metacharacters.
2. Reserved Namespace Collisions: Blocking reserved engine namespaces (`admin`, `postgres`,
   `template0`, `config`, `local`) prevents accidental corruption of core system catalogs.
3. Length Overflow Attacks: Enforcing engine-specific limits (PostgreSQL NAMEDATALEN = 63 bytes,
   MongoDB namespace limit = 63 bytes).
4. CSPRNG Randomness: Generating entropy using OS-level cryptographic RNGs (`secrets` module).
"""

import os
import re
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional
from .exceptions import ConfigurationError, TenantValidationError


# Standard search locations for the Stratum-Core deployment root
DEFAULT_SEARCH_PATHS: List[Path] = [
    Path(os.environ.get("STRATUM_CORE_PATH", "/opt/stratum-core")),
    Path("/opt/stratum-core"),
    Path.cwd() / "stratum-core",
    Path.cwd(),
]

# System-reserved database and role names across Mongo & PostgreSQL
RESERVED_NAMESPACES = {
    "admin", "local", "config", "test",
    "postgres", "template0", "template1", "public",
    "root", "system", "master", "stratum", "stratum_admin", "stratum_db"
}


def find_stratum_root() -> Path:
    """
    Locates the active Stratum-Core repository root directory.

    Returns:
        Path: The absolute path to the Stratum-Core directory.
    """
    for candidate_path in DEFAULT_SEARCH_PATHS:
        if (candidate_path / "dmz" / "docker-compose.yml").exists() and \
           (candidate_path / "database" / "docker-compose.yml").exists():
            return candidate_path.resolve()

    fallback = Path("/opt/stratum-core")
    if fallback.exists():
        return fallback.resolve()

    return Path.cwd().resolve()


def parse_env_file(filepath: Path) -> Dict[str, str]:
    """
    Safely parses a `.env` key-value configuration file without shell execution.

    Junior Study Note:
        Parsing without `eval` or `source` eliminates Shell Injection vulnerabilities.
    """
    env_data: Dict[str, str] = {}
    if not filepath.exists():
        return env_data

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                env_data[key] = val
    return env_data


def get_database_env(root: Optional[Path] = None) -> Dict[str, str]:
    """Retrieves parsed database credentials and configuration."""
    root_path = root or find_stratum_root()
    env_file = root_path / "database" / ".env"
    return parse_env_file(env_file)


def get_gateway_env(root: Optional[Path] = None) -> Dict[str, str]:
    """Retrieves parsed gateway tunnel credentials and active profiles."""
    root_path = root or find_stratum_root()
    env_file = root_path / "gateway" / ".env"
    return parse_env_file(env_file)


def generate_secure_password(length: int = 24) -> str:
    """
    Generates a cryptographically secure, shell-safe alphanumeric password.

    Junior Study Note:
        Characters are selected from an alphanumeric set plus safe punctuation (`!@#%^*-_=+`),
        avoiding single quotes (`'`), double quotes (`"`), backticks (``` ` ```), dollar signs (`$`),
        and backslashes (`\\`) that could cause shell or escaping edge cases.
    """
    alphabet = string.ascii_letters + string.digits + "!@#%^*-_=+"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#%^*-_=+" for c in password)):
            return password


def sanitize_input_string(val: str, max_length: int = 64) -> str:
    """
    Strips dangerous control characters, newlines (CRLF), and truncates to max length.
    """
    if not val:
        return ""
    # Strip carriage returns, newlines, and null bytes (CRLF injection prevention)
    sanitized = re.sub(r"[\r\n\x00-\x1f\x7f-\x9f]", "", val.strip())
    return sanitized[:max_length]


def validate_tenant_identifier(org: str, service: str) -> str:
    """
    Validates and standardizes the tenant namespace pattern: `[org]_[service]`.

    Offensive & Defensive Security Checks:
    1. Rejects path traversal characters (`/`, `\\`, `..`).
    2. Rejects SQL/JS metacharacters (`'`, `"`, `;`, `--`, `/*`, `$`, `{`, `}`).
    3. Prevents namespace collision with reserved system databases.
    4. Enforces the 63-character limit of PostgreSQL identifiers.

    Args:
        org (str): Organization identifier (e.g. 'sgpt').
        service (str): Service identifier (e.g. 'overleaf').

    Returns:
        str: Standardized, validated namespace identifier (e.g., 'sgpt_overleaf').

    Raises:
        TenantValidationError: If identifiers fail security validation.
    """
    clean_org = re.sub(r"[^a-zA-Z0-9]", "", org.strip().lower())
    clean_svc = re.sub(r"[^a-zA-Z0-9_]", "", service.strip().lower())

    if not clean_org:
        raise TenantValidationError(
            f"Invalid organization name: '{org}'. Must contain at least one alphanumeric character."
        )
    if not clean_svc:
        raise TenantValidationError(
            f"Invalid service name: '{service}'. Must contain alphanumeric characters."
        )

    if clean_org in RESERVED_NAMESPACES or clean_svc in RESERVED_NAMESPACES:
        raise TenantValidationError(
            f"Rejected reserved identifier: '{clean_org}' or '{clean_svc}' is a system-reserved namespace."
        )

    db_name = f"{clean_org}_{clean_svc}"

    # PostgreSQL NAMEDATALEN limit is 63 bytes (64 with null terminator)
    if len(db_name) > 63:
        raise TenantValidationError(
            f"Identifier '{db_name}' exceeds the maximum allowed length of 63 characters (length: {len(db_name)})."
        )

    # Database identifiers must start with an alphabetic character or underscore
    if not clean_org[0].isalpha() and clean_org[0] != '_':
        raise TenantValidationError(
            f"Organization identifier '{clean_org}' must start with an alphabetic letter."
        )

    return db_name

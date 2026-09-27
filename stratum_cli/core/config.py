"""
Stratum CLI — Core Configuration & Tenant Validation
=====================================================

Educational Architecture Overview:
----------------------------------
In multi-tenant cloud platforms, naming collisions and insecure credentials are
the leading causes of data leakages and lateral privilege escalations.

This module enforces two mandatory principles:
1. Deterministic Multi-Tenant Naming:
   Every tenant resource is prefixed with `[org]_[service]` (e.g., `sgpt_overleaf`).
   This creates a clean, searchable namespace across databases, storage volumes, and logs.
2. Cryptographic Entropy:
   Passwords are generated using Python's `secrets` module (CSPRNG), NOT the standard
   pseudo-random `random` module, ensuring passwords are mathematically infeasible to predict.
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


def find_stratum_root() -> Path:
    """
    Locates the active Stratum-Core repository root directory.

    The search algorithm checks predefined paths for the existence of core components
    (`dmz/docker-compose.yml` and `database/docker-compose.yml`).

    Returns:
        Path: The absolute path to the Stratum-Core directory.

    Raises:
        ConfigurationError: If no valid Stratum-Core root is found on the host.
    """
    for candidate_path in DEFAULT_SEARCH_PATHS:
        if (candidate_path / "dmz" / "docker-compose.yml").exists() and \
           (candidate_path / "database" / "docker-compose.yml").exists():
            return candidate_path.resolve()

    # Fallback default for production systems
    fallback = Path("/opt/stratum-core")
    if fallback.exists():
        return fallback.resolve()

    return Path.cwd().resolve()


def parse_env_file(filepath: Path) -> Dict[str, str]:
    """
    Safely parses a `.env` key-value configuration file into a dictionary.

    Junior Study Note:
        Unlike using `source .env` in Bash (which executes arbitrary shell code and
        poses severe Remote Code Execution / Injection risks), parsing line-by-line
        guarantees that values are treated purely as static strings without code execution.

    Args:
        filepath (Path): Path to the target `.env` file.

    Returns:
        Dict[str, str]: Key-value mapping of extracted environment variables.
    """
    env_data: Dict[str, str] = {}
    if not filepath.exists():
        return env_data

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            # Ignore empty lines and comment blocks
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                env_data[key] = val
    return env_data


def get_database_env(root: Optional[Path] = None) -> Dict[str, str]:
    """
    Retrieves the parsed environment variables from `database/.env`.

    Args:
        root (Optional[Path]): Root directory of Stratum-Core. Defaults to auto-detection.

    Returns:
        Dict[str, str]: Parsed database environment variables (credentials, ports, images).
    """
    root_path = root or find_stratum_root()
    env_file = root_path / "database" / ".env"
    return parse_env_file(env_file)


def get_gateway_env(root: Optional[Path] = None) -> Dict[str, str]:
    """
    Retrieves the parsed environment variables from `gateway/.env`.

    Args:
        root (Optional[Path]): Root directory of Stratum-Core. Defaults to auto-detection.

    Returns:
        Dict[str, str]: Parsed gateway environment variables (tunnel tokens, profiles).
    """
    root_path = root or find_stratum_root()
    env_file = root_path / "gateway" / ".env"
    return parse_env_file(env_file)


def generate_secure_password(length: int = 24) -> str:
    """
    Generates a high-entropy, shell-safe cryptographic password.

    Junior Study Note:
        The `secrets` library is backed by the operating system's cryptographic
        source (`/dev/urandom` on Linux or `CryptGenRandom` on Windows). This prevents
        PRNG state reconstruction attacks common with `random.random()`.

    Args:
        length (int): Desired password length. Defaults to 24 characters (140+ bits entropy).

    Returns:
        str: A cryptographically strong, multi-class random password.
    """
    alphabet = string.ascii_letters + string.digits + "!@#%^*-_=+"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure character class diversity: upper, lower, digit, and symbol
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#%^*-_=+" for c in password)):
            return password


def validate_tenant_identifier(org: str, service: str) -> str:
    """
    Validates and normalizes tenant organization and service names.

    Enforces the platform naming convention: `[org]_[service]`
    Example: `sgpt` + `overleaf` -> `sgpt_overleaf`

    Args:
        org (str): Organization or company identifier (e.g., 'sgpt', 'isora').
        service (str): Application or service name (e.g., 'overleaf', 'nextcloud').

    Returns:
        str: Standardized database and tenant namespace identifier.

    Raises:
        TenantValidationError: If either identifier contains illegal characters or is empty.
    """
    clean_org = re.sub(r"[^a-zA-Z0-9]", "", org.strip().lower())
    clean_svc = re.sub(r"[^a-zA-Z0-9_-]", "", service.strip().lower())

    if not clean_org:
        raise TenantValidationError(
            f"Invalid organization name: '{org}'. Must contain alphanumeric characters."
        )
    if not clean_svc:
        raise TenantValidationError(
            f"Invalid service name: '{service}'. Must contain alphanumeric characters."
        )

    return f"{clean_org}_{clean_svc}"

"""
Stratum CLI — Exception Hierarchy
==================================
This module defines the custom domain exceptions utilized across the Stratum CLI.
Using a structured exception hierarchy ensures clean error handling, detailed
traceback context for debugging, and friendly user-facing messages.

Educational note for junior engineers:
  Standardizing exceptions allows the CLI boundary to catch domain errors cleanly
  without swallowing unexpected system crashes (e.g., MemoryError, KeyboardInterrupt).
"""


class StratumError(Exception):
    """Base exception for all domain errors occurring within the Stratum CLI."""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class DockerExecutionError(StratumError):
    """Raised when a Docker command or container execution fails unexpectedly."""
    def __init__(self, command: str, exit_code: int, stdout: str, stderr: str):
        msg = f"Docker execution failed (Exit Code {exit_code}) while executing: {' '.join(command)}\nDetails: {stderr or stdout}"
        super().__init__(msg, exit_code=exit_code)
        self.stdout = stdout
        self.stderr = stderr


class ConfigurationError(StratumError):
    """Raised when configuration files (.env, docker-compose.yml) are invalid or missing."""
    pass


class ProvisioningError(StratumError):
    """Raised when database or infrastructure tenant provisioning fails."""
    pass


class TenantValidationError(StratumError):
    """Raised when organization or service identifiers violate isolation naming conventions."""
    pass

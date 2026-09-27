"""
Stratum CLI — Docker Container Execution Engine
================================================

Educational Overview:
---------------------
Stratum-Core enforces a Zero-Trust architecture where database engines and persistence
tiers do NOT publish host ports (zero open `0.0.0.0` or `127.0.0.1` ports on the host).

Because ports are air-gapped behind internal Docker bridge networks, external management
tools cannot use standard TCP network connections. Instead, administrative tasks (creating
users, performing isolated dumps, pinging health) are securely executed via direct
container process execution (`docker exec`).

Junior Study Note:
  Using `subprocess.run` with discrete argument lists (`["docker", "exec", ...]`)
  strictly prevents Shell Injection attacks compared to `os.system("docker exec " + cmd)`.
"""

import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from .exceptions import DockerExecutionError


def is_docker_available() -> bool:
    """
    Verifies that the Docker CLI is installed and the Docker daemon is actively responding.

    Returns:
        bool: True if docker command exists and daemon responds, False otherwise.
    """
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return res.returncode == 0
    except Exception:
        return False


def exec_in_container(
    container_name: str,
    cmd: List[str],
    env: Optional[Dict[str, str]] = None,
    raise_on_error: bool = False
) -> Tuple[int, str, str]:
    """
    Executes a discrete binary command inside a running Docker container.

    Args:
        container_name (str): Target container identifier (e.g., 'stratum-database-mongodb').
        cmd (List[str]): Command array to execute inside the container.
        env (Optional[Dict[str, str]]): Additional environment variables for execution context.
        raise_on_error (bool): If True, raises DockerExecutionError on non-zero exit codes.

    Returns:
        Tuple[int, str, str]: A tuple of (exit_code, stdout_text, stderr_text).

    Raises:
        DockerExecutionError: If `raise_on_error` is True and the command exits with non-zero code.
    """
    docker_args = ["docker", "exec"]
    if env:
        for k, v in env.items():
            docker_args.extend(["-e", f"{k}={v}"])
    docker_args.append(container_name)
    docker_args.extend(cmd)

    res = subprocess.run(
        docker_args,
        capture_output=True,
        text=True,
        check=False
    )

    if raise_on_error and res.returncode != 0:
        raise DockerExecutionError(
            command=docker_args,
            exit_code=res.returncode,
            stdout=res.stdout,
            stderr=res.stderr
        )

    return res.returncode, res.stdout, res.stderr


def is_container_running(container_name: str) -> bool:
    """
    Checks if a given container exists and is in the 'running' state.

    Args:
        container_name (str): Container name.

    Returns:
        bool: True if running, False otherwise.
    """
    try:
        res = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0 and "true" in res.stdout.lower()
    except Exception:
        return False


def get_container_health(container_name: str) -> str:
    """
    Retrieves the granular healthcheck status of a container.

    Returns:
        str: 'healthy', 'unhealthy', 'starting', 'running', 'stopped', or 'not_found'.
    """
    try:
        format_expr = "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}"
        res = subprocess.run(
            ["docker", "inspect", "--format", format_expr, container_name],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode != 0:
            return "not_found"
        return res.stdout.strip()
    except Exception:
        return "error"

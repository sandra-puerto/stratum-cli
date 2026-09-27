# Stratum-CLI

[![CLI Version](https://img.shields.io/badge/CLI-v1.0.0-6366f1?style=for-the-badge&logo=gnubash&logoColor=white)](https://github.com/sandrapuerto/stratum-cli)
[![Platform](https://img.shields.io/badge/Platform-Stratum%20Core-4f46e5?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/sandrapuerto/stratum-core)
[![Architect](https://img.shields.io/badge/Architect-Sandra%20Puerto-f59e0b?style=for-the-badge&logo=linkedin&logoColor=white)](https://sandrapuerto.com)
[![License](https://img.shields.io/badge/License-Enhanced%20MIT-10b981?style=for-the-badge)](LICENSE)

> **Autonomous Multi-Tenant Persistence & Lifecycle Orchestrator for Stratum-Core.**  
> *Isolation by design, not by discipline.*  
> 
> 📖 **[Guía de Uso & Manual de Operaciones en Español](docs/MANUAL_DE_USO.md)**

---

## 1. Overview

`stratum-cli` is the command-line orchestrator designed to operate and automate multi-organization infrastructure running on **[Stratum-Core](https://github.com/sandrapuerto/stratum-core)**.

It eliminates manual database scripting, human configuration errors, and tunnel drift by providing deterministic, zero-dependency management commands.

```
       stratum db create <org> <service> --engine [mongo|postgres]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       MongoDB Engine                   PostgreSQL Engine
   [org]_[service] (DB)              [org]_[service] (DB)
   [org] (readWrite User)            [org] (Owner Role)
   Auto-Generated Password           Auto-Generated Password
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     Output Ready-to-Copy .env
```

---

## 2. Key Features

- 🔒 **Deterministic Naming Pattern:** Enforces `[org]_[service]` (e.g. `sgpt_overleaf`, `isora_portal`, `client_nextcloud`).
- 🔑 **Cryptographic Password Generation:** Generates 24-character high-entropy alphanumeric credentials automatically.
- ⚡ **Zero External Dependencies:** Built with Python standard library (`subprocess`, `argparse`, `secrets`) to run immediately on any Linux host.
- 🛡️ **Isolated Tenant Backups:** Creates compressed, isolated database dumps (`.archive.gz` / `.pgdump`) without touching other tenants.
- 🌐 **Gateway Tenant Registration:** Auto-registers Cloudflare Zero Trust tunnel tokens and profiles in `gateway/.env`.
- 🩺 **Health & Status Inspector:** Real-time visibility into the health of all platform containers.

---

## 3. Installation

### Quick Install on Ubuntu VPS

```bash
# Clone the repository
git clone https://github.com/sandrapuerto/stratum-cli.git /opt/stratum-cli

# Run the installer (installs /usr/local/bin/stratum)
sudo bash /opt/stratum-cli/install.sh
```

### Or Install via Python / Pip

```bash
pip install -e /opt/stratum-cli
```

Verify the installation:
```bash
stratum --help
stratum status
```

---

## 4. Command Reference & Examples

### 4.1 Provision a Tenant Database (`stratum db create`)

Creates an isolated database, creates the application user, sets permissions, and prints the connection strings ready for the tenant's `.env`:

#### MongoDB Example (e.g. Overleaf):
```bash
stratum db create sgpt overleaf --engine mongo
```
**Output:**
```text
========================================================================
[+] STRATUM MULTI-TENANT PROVISIONING SUCCESSFUL (MongoDB)
========================================================================
  Tenant Database .... : sgpt_overleaf
  Application User ... : sgpt
  Generated Password . : K9x#mP2vL!8wQzRtY4uX7nB1
  Proxy Boundary Host  : stratum-database-nginx:27017
  Auth Source ........ : sgpt_overleaf
------------------------------------------------------------------------
  Copy-Paste for Tenant .env file:

# --- Stratum Boundary Persistence (Tenant: SGPT) ---
STRATUM_DB_HOST=stratum-database-nginx
MONGO_APP_USER=sgpt
MONGO_APP_PASSWORD=K9x#mP2vL!8wQzRtY4uX7nB1
MONGO_DB_NAME=sgpt_overleaf
MONGO_AUTH_SOURCE=sgpt_overleaf
MONGO_URL=mongodb://sgpt:K9x#mP2vL!8wQzRtY4uX7nB1@stratum-database-nginx:27017/sgpt_overleaf?authSource=sgpt_overleaf
========================================================================
```

#### PostgreSQL Example (e.g. Nextcloud / Strapi):
```bash
stratum db create isora nextcloud --engine postgres
```

---

### 4.2 Backup a Tenant Database (`stratum backup`)

Creates an isolated, compressed dump of only that specific client's data:

```bash
stratum backup sgpt overleaf --engine mongo
```
*Output: `/opt/backups/sgpt/sgpt_overleaf_20260927_054500.archive.gz`*

---

### 4.3 Register a Gateway Tunnel (`stratum gateway add`)

Registers a new organization's Cloudflare Zero Trust tunnel token in `gateway/.env` and updates `COMPOSE_PROFILES`:

```bash
stratum gateway add CLIENT_X --token "eyJh...token..."
```

---

---

### 4.4 List Available Persistence Drivers (`stratum db list-engines`)

```bash
stratum db list-engines
```

---

### 4.5 Inspect Platform Health (`stratum status`)

```bash
stratum status
```

---

### 4.6 System Diagnostics & Doctor (`stratum doctor`)

Runs a deep audit of Linux kernel parameters (`vm.overcommit_memory`), secret `.env` file permissions, Docker daemon health, and shared DMZ network state:

```bash
stratum doctor
```

---

## 5. Developer Guide: How to Add a New Database Engine

`stratum-cli` uses the **Strategy & Registry Pattern**. Adding support for a new engine (e.g. MariaDB, ClickHouse, SQLite) takes less than 30 lines of code without touching the core CLI:

1. Create a new file `stratum_cli/engines/mariadb.py`:
   ```python
   from .base import BaseDatabaseEngine, ProvisioningResult, register_engine

   @register_engine("mariadb")
   class MariaDBEngine(BaseDatabaseEngine):
       @property
       def engine_name(self) -> str:
           return "MariaDB Relational Engine"

       @property
       def target_container(self) -> str:
           return "stratum-database-mariadb"

       def provision(self, org: str, service: str, password=None) -> ProvisioningResult:
           # Implement provisioning logic via exec_in_container
           ...

       def backup(self, org: str, service: str, output_dir) -> Path:
           # Implement streaming dump via mysqldump
           ...
   ```
2. Import the new class in `stratum_cli/engines/__init__.py`.
3. The new engine will immediately be available in `stratum db create <org> <service> -e mariadb` and `stratum db list-engines`.

---

## 6. Architectural Credits & Author

**Stratum-CLI** was architected and implemented by **Sandra Gabriela Puerto Torres** as part of the Stratum Platform ecosystem.

* **Website:** [https://sandrapuerto.com](https://sandrapuerto.com)
* **Email:** [contacto@sandrapuerto.com](mailto:contacto@sandrapuerto.com)
* **Core Platform:** [Stratum-Core](https://github.com/sandrapuerto/stratum-core)

---

## 7. License

This project is licensed under the **Enhanced MIT License with Mandatory Architectural Attribution**. See the [LICENSE](LICENSE) file for details.

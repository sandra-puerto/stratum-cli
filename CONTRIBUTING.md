# Contributing to Stratum-CLI

Thank you for your interest in improving **Stratum-CLI**!

---

## 1. Architectural Philosophy

Every feature or pull request must adhere to the following principles:

1. **Zero Unnecessary Dependencies:** The CLI relies strictly on the Python standard library to ensure seamless execution across any Linux host without complex virtual environment overhead.
2. **Deterministic Multi-Tenant Naming:** All database provisioners must enforce the `[org]_[service]` convention.
3. **Security by Default:** Passwords must be generated with cryptographically secure random sources (`secrets` module).
4. **Idempotence:** Running commands multiple times should produce consistent, non-destructive results.

---

## 2. Development Setup

```bash
# Clone the repository
git clone https://github.com/sandrapuerto/stratum-cli.git
cd stratum-cli

# Install in editable mode
pip install -e .

# Test CLI
stratum --help
```

---

## 3. Pull Request Guidelines

1. Ensure code passes PEP 8 formatting.
2. Keep commands modular within `stratum_cli/commands/`.
3. Submit PRs against the `main` branch.

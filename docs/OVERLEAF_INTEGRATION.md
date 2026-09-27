# Overleaf Community Edition Integration & Architecture
**Platform:** Stratum-Core Orchestration Engine  
**Author:** Sandra Gabriela Puerto Torres  

---

## 1. Architectural Overview

The integration between **Stratum-Core** and **Overleaf Community Edition** follows a strict separation of concerns, ensuring maximum tenant isolation and performance.

### 1.1 The Multi-Tenant Persistence Layer
Overleaf relies heavily on two persistence engines provided by `stratum-database`:
- **MongoDB:** Serves as the primary document store for users, projects, and metadata. Each tenant gets an isolated database (e.g., `sgpt_overleaf`) provisioned automatically via `stratum db create`.
- **Redis:** Used for real-time operational states (document locks, collaborative sessions, pub/sub for the compiler). All tenants connect via the internal Layer 4 boundary proxy.

### 1.2 The Gateway Layer
External requests reach Overleaf through the **Stratum Gateway**:
1. **Cloudflare Zero Trust Tunnel** (`stratum-gateway-cloudflared-<org>`) routes authenticated traffic to the internal proxy.
2. **Nginx Proxy Manager** (NPM) decrypts SSL and applies WebSockets forwarding (crucial for real-time collaboration).
3. Traffic is forwarded over the isolated `stratum_dmz` Docker network directly to the specific Overleaf tenant container.

---

## 2. Limitations of Overleaf Community Edition

When deploying Overleaf in a multi-tenant corporate or educational environment, it is critical to understand the built-in constraints of the open-source **Community Edition (CE)** versus Server Pro.

### 2.1 Missing Access Control & LDAP
- **No SSO/SAML/LDAP:** CE does not natively support SSO or Active Directory integration. Users must sign up manually.
- **Admin Panel:** CE lacks an internal administrative panel for managing users across the instance.
- *Mitigation:* Stratum handles security at the Gateway layer using **Cloudflare Access**, providing an external IdP (Google, Azure AD, SAML) before any request even touches Overleaf.

### 2.2 Compilation Limits & Timeout Edge Cases
- **Single Server Compiler:** CE runs the LaTeX compiler locally inside the container (or heavily relies on a single host thread). It lacks the distributed compilation farm available in Pro.
- **Timeout Edge Case:** Large LaTeX documents (especially TikZ diagrams or heavy bibliographies) might hit the default compiler timeout.
- *Mitigation:* Ensure `docker-compose.yml` for Overleaf specifies appropriate limits and modify the Overleaf settings (`TEX_LIVE_DOCKER_IMAGE`) if full TeXLive is needed instead of the minimal image.

### 2.3 Collaboration Limitations
- **Track Changes & History:** Advanced track changes, full project history (Git integration), and sync features are locked behind the Pro version.
- **Chat:** The internal chat module is often disabled or unsupported in CE.

---

## 3. Known Edge Cases in Stratum Environments

### 3.1 WebSockets & Real-time Collaboration (NPM Settings)
Overleaf requires WebSockets for real-time typing. If users complain about "Connection Lost" or "Reconnecting...", the edge case is usually in the Gateway:
- **Solution:** Ensure that in Nginx Proxy Manager (NPM), the option **"WebSockets Support"** is strictly enabled for the proxy host pointing to the tenant's Overleaf instance.

### 3.2 LaTeX Compiler Sandboxing (Docker in Docker)
By default, Overleaf Sandboxed compiles use Docker inside Docker (DinD) for security.
- **Limitation:** In highly restricted environments (like Stratum's security baseline with `no-new-privileges`), mapping `/var/run/docker.sock` to the tenant container can create a privilege escalation vector.
- **Mitigation:** Stratum strongly recommends using local compilation instead of sandboxed DinD for trusted multi-tenant internal environments, or isolating the compiler node entirely. Set `SHARELATEX_ALLOW_PUBLIC_ACCESS=false`.

### 3.3 MongoDB Authentication Delays
During initial provisioning of a heavy VPS load, MongoDB might take up to 30 seconds to become healthy.
- **Edge Case:** If `stratum db create` is run exactly as MongoDB is initializing its WiredTiger cache, `mongosh` might throw an EOF error.
- **Mitigation:** `stratum-cli` relies on healthchecks. Ensure the core database stack is marked as `healthy` before provisioning.

---

## 4. Best Practices for Junior Engineers

1. **Never share the root MongoDB password:** Always use `stratum db create <org> <service> -e mongo` to generate a restricted, unique user.
2. **Review Gateway Rules:** When adding a tenant via `stratum gateway add`, remember that the Cloudflare Tunnel must have the correct Access Policies to prevent unauthorized registration on the Overleaf instance.
3. **Backups are Per-Tenant:** Run `stratum backup` regularly. Overleaf project data cannot be reconstructed if MongoDB is lost.

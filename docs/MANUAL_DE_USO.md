# Manual de Operaciones y Guía de Uso — Stratum-CLI

**Plataforma:** Stratum-Core Orchestration Engine  
**Versión de CLI:** 1.0.0  
**Arquitecta / Autora:** Sandra Gabriela Puerto Torres  
**Sitio Web:** [https://sandrapuerto.com](https://sandrapuerto.com)  

---

## 📖 Tabla de Contenidos
1. [Introducción y Conceptos Básicos](#1-introducción-y-conceptos-básicos)
2. [Instalación en el Servidor (VPS)](#2-instalación-en-el-servidor-vps)
3. [Flujo 1: Aprovisionar Base de Datos para un Cliente](#3-flujo-1-aprovisionar-base-de-datos-para-un-cliente)
4. [Flujo 2: Registrar Túnel de Cloudflare en el Gateway](#4-flujo-2-registrar-túnel-de-cloudflare-en-el-gateway)
5. [Flujo 3: Respaldos (Backups) y Restauración](#5-flujo-3-respaldos-backups-y-restauración)
6. [Flujo 4: Monitoreo, Salud y Diagnóstico (Doctor)](#6-flujo-4-monitoreo-salud-y-diagnóstico-doctor)
7. [Tabla Rápida de Comandos (Cheat Sheet)](#7-tabla-rápida-de-comandos-cheat-sheet)

---

## 1. Introducción y Conceptos Básicos

`stratum-cli` es la herramienta de línea de comandos creada para automatizar la gestión multi-empresa sobre **Stratum-Core**.

### Regla de Oro: Patrón de Nombres `[organizacion]_[servicio]`
Cada recurso creado en las bases de datos o en el almacenamiento siempre sigue el formato:
$$\text{Nombre de Base de Datos} = \text{organizacion}\_\text{servicio}$$

* **Ejemplo 1:** Para la empresa **SGPT** y su plataforma **Overleaf**, la base de datos se llamará `sgpt_overleaf` y el usuario de base de datos será `sgpt`.
* **Ejemplo 2:** Para la empresa **Isora** y su app **Nextcloud**, la base de datos se llamará `isora_nextcloud` y el usuario será `isora`.

---

## 2. Instalación en el Servidor (VPS)

### Paso 1: Copiar o clonar `stratum-cli`
En tu VPS (como usuario con privilegios `sudo`):

```bash
# Copiar stratum-cli a /opt/stratum-cli
sudo cp -r /home/cto/stratum-cli /opt/stratum-cli
```

### Paso 2: Ejecutar el instalador global
```bash
sudo bash /opt/stratum-cli/install.sh
```

### Paso 3: Verificar la instalación
```bash
stratum --help
```
*Si ves el menú de ayuda, ¡el comando global `stratum` ya está instalado en `/usr/local/bin/stratum`!*

> **Tip de Idioma:** Puedes cambiar el idioma de la terminal en cualquier momento con `-l es` o `-l en`. Ejemplo: `stratum -l es doctor`.

---

## 3. Flujo 1: Aprovisionar Base de Datos para un Cliente

Para crear una base de datos aislada sin entrar manualmente a Docker ni a las consolas de bases de datos:

### A. Para aplicaciones basadas en MongoDB (ej. Overleaf)

Ejecuta:
```bash
stratum db create sgpt overleaf --engine mongo
```

**Lo que hace Stratum-CLI por ti:**
1. Genera una contraseña criptográfica segura de 24 caracteres.
2. Entra al contenedor `stratum-database-mongodb`.
3. Crea la base de datos `sgpt_overleaf`.
4. Crea el usuario `sgpt` y le asigna permisos exclusivos sobre `sgpt_overleaf`.
5. Te imprime en pantalla el bloque listo para copiar y pegar en el archivo `.env` del cliente:

```dotenv
# --- Stratum Boundary Persistence (Tenant: SGPT) ---
STRATUM_DB_HOST=stratum-database-nginx
MONGO_APP_USER=sgpt
MONGO_APP_PASSWORD=una_clave_generada_aleatoria_123
MONGO_DB_NAME=sgpt_overleaf
MONGO_AUTH_SOURCE=sgpt_overleaf
MONGO_URL=mongodb://sgpt:una_clave_generada_aleatoria_123@stratum-database-nginx:27017/sgpt_overleaf?authSource=sgpt_overleaf
```

---

### B. Para aplicaciones basadas en PostgreSQL (ej. Nextcloud, Strapi, APIs SQL)

Ejecuta:
```bash
stratum db create isora nextcloud --engine postgres
```

Te generará el usuario `isora`, la base de datos `isora_nextcloud` y la variable:
```dotenv
DATABASE_URL=postgresql://isora:clave_aleatoria@stratum-database-nginx:5432/isora_nextcloud
```

---

### C. Para aplicaciones que consumen Redis (Cache / Colas / WebSockets)

Ejecuta:
```bash
stratum db create sgpt overleaf --engine redis
```
Te imprimirá las variables de conexión hacia el Boundary Proxy de Redis (`stratum-database-nginx:6379`).

---

## 4. Flujo 2: Registrar Túnel de Cloudflare en el Gateway

Cuando incorpores un nuevo tenant o empresa que tenga su propia cuenta de Cloudflare Zero Trust:

### Paso 1: Ejecutar el registro
```bash
stratum gateway add CLIENTE_B --token "eyJh...tu_token_de_cloudflare..."
```

**Lo que hace el CLI:**
- Guarda de forma segura el token en `/opt/stratum-core/gateway/.env`.
- Actualiza la variable `COMPOSE_PROFILES` agregando el nuevo perfil sin borrar los anteriores.

### Paso 2: Recargar el Gateway sin caídas
```bash
cd /opt/stratum-core/gateway && docker compose up -d
```
Docker levantará el nuevo túnel en paralelo sin reiniciar ni afectar a los túneles que ya estén funcionando.

---

## 5. Flujo 3: Respaldos (Backups) y Restauración

### Crear un Backup Aislado por Cliente
Los backups se guardan comprimidos en `/opt/backups/<organizacion>/`:

```bash
# Backup de MongoDB para SGPT
stratum backup sgpt overleaf --engine mongo

# Backup de PostgreSQL para Isora
stratum backup isora nextcloud --engine postgres
```

*Resultado generado:*
`/opt/backups/sgpt/sgpt_overleaf_20260927_054500.archive.gz`

---

### Cómo Restaurar un Backup en caso de emergencia

#### Restaurar MongoDB:
```bash
docker exec -i stratum-database-mongodb mongorestore -u stratum_admin -p TU_PASSWORD_ROOT --authenticationDatabase admin --nsInclude="sgpt_overleaf.*" --gzip --archive < /opt/backups/sgpt/sgpt_overleaf_20260927_054500.archive.gz
```

#### Restaurar PostgreSQL:
```bash
docker exec -i stratum-database-postgres pg_restore -U stratum_admin -d isora_nextcloud --clean < /opt/backups/isora/isora_nextcloud_20260927_054500.pgdump
```

---

## 6. Flujo 4: Monitoreo, Salud y Diagnóstico (Doctor)

### A. Diagnóstico General del Sistema (`stratum doctor`)
Verifica parámetros del kernel, permisos de archivos `.env` (que tengan `chmod 600`), redes Docker y estado general:

```bash
stratum doctor
```

### B. Estado en Tiempo Real de los Contenedores (`stratum status`)
Muestra el estado de salud de toda la plataforma:

```bash
stratum status
```

---

## 7. Tabla Rápida de Comandos (Cheat Sheet)

| Tarea / Operación | Comando CLI |
|---|---|
| **Crear BD MongoDB para un cliente** | `stratum db create <org> <servicio> -e mongo` |
| **Crear BD PostgreSQL para un cliente** | `stratum db create <org> <servicio> -e postgres` |
| **Listar motores disponibles** | `stratum db list-engines` |
| **Crear Backup de un cliente** | `stratum backup <org> <servicio> -e mongo` |
| **Registrar Túnel Cloudflare de cliente** | `stratum gateway add <ORG> -t "<token>"` |
| **Ver estado y salud de contenedores** | `stratum status` |
| **Ejecutar auditoría y diagnóstico del VPS** | `stratum doctor` |
| **Ejecutar cualquier comando en Español** | `stratum -l es <comando>` |
| **Ejecutar cualquier comando en Inglés** | `stratum -l en <comando>` |

---

> **Mantenimiento y Soporte:** Para dudas o reportes técnicos, contactar a **contacto@sandrapuerto.com**.

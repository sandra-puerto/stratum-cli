"""
Stratum CLI — Internationalization (i18n) & Localization Engine
===============================================================

Educational Overview:
---------------------
This module provides lightweight, zero-dependency localization support.
Language selection is resolved using the following precedence order:
1. Explicit CLI argument: `--lang es` or `--lang en`
2. Environment variable: `STRATUM_LANG=es`
3. Operating system locale: `LC_ALL` or `LANG` (e.g., `es_CO.UTF-8` -> `es`)
4. Fallback default: English (`en`)
"""

import os
import locale
from typing import Dict, Any


_CURRENT_LANG = "en"

# Catalog of localized strings
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # General & CLI
        "cli_desc": "Stratum CLI — Autonomous Multi-Tenant Persistence & Lifecycle Orchestrator",
        "cli_epilog": "Engineered by Sandra Gabriela Puerto Torres — https://sandrapuerto.com",
        "lang_help": "Override CLI language (en, es)",
        
        # Commands descriptions
        "cmd_db": "Database & multi-tenant persistence provisioning",
        "cmd_db_create": "Create an isolated tenant database & dedicated user",
        "cmd_db_list": "List all registered persistence engine providers",
        "cmd_gw": "Gateway & Cloudflare Zero Trust tunnel management",
        "cmd_gw_add": "Register a tenant Cloudflare tunnel in gateway/.env",
        "cmd_bk": "Isolated tenant database backup & dump",
        "cmd_status": "Inspect platform health and running container topology",
        "cmd_doctor": "Run system diagnostics, kernel check, and security audit",
        
        # Arguments
        "arg_org": "Organization identifier (e.g., 'sgpt', 'isora')",
        "arg_service": "Service name (e.g., 'overleaf', 'nextcloud')",
        "arg_engine": "Persistence engine (default: mongo)",
        "arg_password": "Custom password (optional; auto-generates 24-char cryptographic password)",
        "arg_token": "Cloudflare Tunnel token from Zero Trust dashboard",
        "arg_output_dir": "Target backup directory (default: /opt/backups)",
        
        # Provisioning Success Messages
        "prov_success_title": "[+] STRATUM MULTI-TENANT PROVISIONING SUCCESSFUL ({engine})",
        "prov_org": "  Organization ....... : {org}",
        "prov_service": "  Service ............ : {service}",
        "prov_db": "  Tenant Database .... : {db}",
        "prov_user": "  Application User ... : {user}",
        "prov_password": "  Generated Password . : {password}",
        "prov_proxy": "  Boundary Proxy ..... : {host}:{port}",
        "prov_uri_header": "  Connection URI:",
        "prov_env_header": "  Copy-Paste for Tenant .env file:",
        
        # Backup Messages
        "bk_success_title": "[+] STRATUM TENANT BACKUP COMPLETED ({engine})",
        "bk_artifact": "  Artifact ........... : {file}",
        "bk_size": "  Archive Size ....... : {size} KB",
        "bk_error": "[-] Backup Error: {err}",
        
        # Gateway Messages
        "gw_success_title": "[+] STRATUM GATEWAY TENANT REGISTRATION SUCCESSFUL",
        "gw_token_stored": "  Tunnel Token ....... : {token}... (persisted in gateway/.env)",
        "gw_target_file": "  Target File ........ : {file}",
        "gw_reload_hint": "  To activate this tenant tunnel immediately on your VPS without downtime:\n  $ cd /opt/stratum-core/gateway && docker compose up -d",
        
        # Doctor Diagnostics
        "doc_title": " STRATUM PLATFORM DIAGNOSTICS & SYSTEM DOCTOR",
        "doc_pass": "[PASS]",
        "doc_warn": "[WARN]",
        "doc_fail": "[FAIL]",
        "doc_info": "[INFO]",
        "doc_docker_ok": "1. Docker Daemon: Responsive and accessible.",
        "doc_docker_fail": "1. Docker Daemon: Not running or current user lacks docker group privileges.",
        "doc_root_ok": "2. Stratum Core Root: Located at '{root}'.",
        "doc_root_warn": "2. Stratum Core Root: Not found at standard locations (/opt/stratum-core).",
        "doc_dmz_ok": "3. Shared DMZ Network: 'stratum_dmz' is active.",
        "doc_dmz_warn": "3. Shared DMZ Network: 'stratum_dmz' not found. Run 'docker compose up -d' in dmz/.",
        "doc_dmz_fail": "3. Shared DMZ Network: Unable to inspect docker networks.",
        "doc_overcommit_ok": "4. Kernel Overcommit: vm.overcommit_memory is tuned to '1'.",
        "doc_overcommit_warn": "4. Kernel Overcommit: vm.overcommit_memory is '{val}' (recommended: '1' for Redis).",
        "doc_overcommit_skip": "4. Kernel Overcommit: Not a Linux host (skipping /proc check).",
        "doc_perm_ok": "5. File Permissions: Secret .env files are secure.",
        "doc_perm_warn": "5. Permissions: '{file}' has permissions {mode} (recommended: chmod 600).",
        "doc_summary": " Diagnostic Summary: {passed}/{total} checks passed.",
        
        # Status Messages
        "status_title": " STRATUM-CORE — PLATFORM STATUS & HEALTH OVERVIEW",
        "status_col_role": "COMPONENT / ROLE",
        "status_col_container": "CONTAINER NAME",
        "status_col_health": "STATUS",
    },
    
    "es": {
        # General & CLI
        "cli_desc": "Stratum CLI — Orquestador de Persistencia y Ciclo de Vida Multi-Inquilino",
        "cli_epilog": "Diseñado por Sandra Gabriela Puerto Torres — https://sandrapuerto.com",
        "lang_help": "Cambiar idioma de la terminal (en, es)",
        
        # Commands descriptions
        "cmd_db": "Aprovisionamiento de bases de datos y persistencia multi-empresa",
        "cmd_db_create": "Crea una base de datos aislada y un usuario dedicado para el inquilino",
        "cmd_db_list": "Lista todos los motores de persistencia registrados",
        "cmd_gw": "Gestión del Gateway y túneles Cloudflare Zero Trust",
        "cmd_gw_add": "Registra un túnel Cloudflare de cliente en gateway/.env",
        "cmd_bk": "Copia de seguridad y volcado aislado de base de datos",
        "cmd_status": "Inspecciona la salud y topología de los contenedores en ejecución",
        "cmd_doctor": "Ejecuta diagnóstico del sistema, parámetros del kernel y auditoría de seguridad",
        
        # Arguments
        "arg_org": "Identificador de la organización/empresa (ej., 'sgpt', 'isora')",
        "arg_service": "Nombre del servicio/aplicación (ej., 'overleaf', 'nextcloud')",
        "arg_engine": "Motor de persistencia (por defecto: mongo)",
        "arg_password": "Clave personalizada (opcional; genera 24 caracteres criptográficos por defecto)",
        "arg_token": "Token del túnel Cloudflare emitido en Zero Trust dashboard",
        "arg_output_dir": "Directorio destino del backup (por defecto: /opt/backups)",
        
        # Provisioning Success Messages
        "prov_success_title": "[+] APROVISIONAMIENTO MULTI-INQUILINO STRATUM EXITOSO ({engine})",
        "prov_org": "  Organización ....... : {org}",
        "prov_service": "  Servicio ........... : {service}",
        "prov_db": "  Base de Datos ...... : {db}",
        "prov_user": "  Usuario Aplicación . : {user}",
        "prov_password": "  Contraseña Generada  : {password}",
        "prov_proxy": "  Proxy de Frontera .. : {host}:{port}",
        "prov_uri_header": "  URI de Conexión:",
        "prov_env_header": "  Copiar y Pegar en el archivo .env del Tenant:",
        
        # Backup Messages
        "bk_success_title": "[+] RESPALDO DE INQUILINO STRATUM COMPLETADO ({engine})",
        "bk_artifact": "  Archivo Generado ... : {file}",
        "bk_size": "  Tamaño del Archivo . : {size} KB",
        "bk_error": "[-] Error en Backup: {err}",
        
        # Gateway Messages
        "gw_success_title": "[+] REGISTRO DE TÚNEL EN STRATUM GATEWAY EXITOSO",
        "gw_token_stored": "  Token del Túnel .... : {token}... (guardado en gateway/.env)",
        "gw_target_file": "  Archivo Destino .... : {file}",
        "gw_reload_hint": "  Para activar este túnel en tu VPS sin interrumpir el servicio:\n  $ cd /opt/stratum-core/gateway && docker compose up -d",
        
        # Doctor Diagnostics
        "doc_title": " DIAGNÓSTICO DE PLATAFORMA Y DOCTOR DEL SISTEMA STRATUM",
        "doc_pass": "[CORRECTO]",
        "doc_warn": "[AVISO]",
        "doc_fail": "[FALLO]",
        "doc_info": "[INFO]",
        "doc_docker_ok": "1. Demonio Docker: Activo y accesible.",
        "doc_docker_fail": "1. Demonio Docker: No está corriendo o el usuario no pertenece al grupo docker.",
        "doc_root_ok": "2. Directorio Stratum Core: Localizado en '{root}'.",
        "doc_root_warn": "2. Directorio Stratum Core: No encontrado en rutas estándar (/opt/stratum-core).",
        "doc_dmz_ok": "3. Red Compartida DMZ: 'stratum_dmz' está activa.",
        "doc_dmz_warn": "3. Red Compartida DMZ: 'stratum_dmz' no encontrada. Ejecuta 'docker compose up -d' en dmz/.",
        "doc_dmz_fail": "3. Red Compartida DMZ: No fue posible inspeccionar redes docker.",
        "doc_overcommit_ok": "4. Kernel Overcommit: vm.overcommit_memory está configurado en '1'.",
        "doc_overcommit_warn": "4. Kernel Overcommit: vm.overcommit_memory es '{val}' (recomendado: '1' para Redis).",
        "doc_overcommit_skip": "4. Kernel Overcommit: No es un sistema Linux (omitiendo verificación /proc).",
        "doc_perm_ok": "5. Permisos de Archivos: Archivos .env confidenciales están protegidos.",
        "doc_perm_warn": "5. Permisos: '{file}' tiene permisos {mode} (recomendado: chmod 600).",
        "doc_summary": " Resumen del Diagnóstico: {passed}/{total} verificaciones pasadas.",
        
        # Status Messages
        "status_title": " STRATUM-CORE — ESTADO DE PLATAFORMA Y SALUD EN TIEMPO REAL",
        "status_col_role": "COMPONENTE / ROL",
        "status_col_container": "NOMBRE DEL CONTENEDOR",
        "status_col_health": "ESTADO",
    }
}


def detect_system_language() -> str:
    """Detects default language from environment or system locale."""
    # 1. Check STRATUM_LANG environment variable
    env_lang = os.environ.get("STRATUM_LANG", "").lower().strip()
    if env_lang in ("es", "spanish", "español"):
        return "es"
    if env_lang in ("en", "english"):
        return "en"

    # 2. Check system locale
    try:
        sys_loc = locale.getdefaultlocale()[0] or ""
        if sys_loc.lower().startswith("es"):
            return "es"
    except Exception:
        pass

    return "en"


def set_language(lang: str):
    """Explicitly sets the active language for the CLI session."""
    global _CURRENT_LANG
    clean_lang = lang.lower().strip()
    if clean_lang in TRANSLATIONS:
        _CURRENT_LANG = clean_lang
    else:
        _CURRENT_LANG = "en"


def get_language() -> str:
    """Returns current active language code."""
    return _CURRENT_LANG


def t(key: str, **kwargs: Any) -> str:
    """
    Translates a translation key to the active language with formatted parameters.

    Args:
        key (str): Translation key identifier.
        **kwargs: Dynamic interpolation variables.

    Returns:
        str: Localized and formatted message.
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANG, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


# Initialize language on module import
set_language(detect_system_language())

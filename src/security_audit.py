import re

import pandas as pd

from config import (
    BASE_DIR,
    DATABASE_FILE,
    LOG_FILE,
    MODEL_FILE,
    RESULTS_DIR,
    SECURITY_REPORT_FILE,
    SECURITY_RISK_FILE,
)


SENSITIVE_COLUMNS = {
    "person_age": "dato personal indirecto",
    "person_gender": "dato personal indirecto",
    "person_education": "dato personal indirecto",
    "person_income": "dato financiero",
    "person_emp_exp": "dato laboral",
    "credit_score": "dato financiero",
    "previous_loan_defaults_on_file": "historial financiero",
    "loan_status": "resultado financiero",
}


def run_security_audit(df, logger):
    logger.info("Etapa 9: auditoría de seguridad")
    exposed = scan_exposed_credentials()
    env_exists = (BASE_DIR / ".env").exists()
    env_ignored = is_env_ignored()
    permissions = inspect_permissions([DATABASE_FILE, LOG_FILE, MODEL_FILE])

    risks = build_risk_matrix(exposed, env_ignored, permissions)
    risks.to_csv(SECURITY_RISK_FILE, index=False)
    report = build_report(df, exposed, env_exists, env_ignored, permissions, risks)
    SECURITY_REPORT_FILE.write_text(report, encoding="utf-8")
    logger.info("Informe de seguridad guardado en: %s", SECURITY_REPORT_FILE)
    return risks


def scan_exposed_credentials():
    patterns = [
        re.compile(r"(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ]
    findings = []
    allowed_extensions = {".py", ".md", ".txt", ".yml", ".yaml", ".json", ".ps1"}
    for path in BASE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed_extensions:
            continue
        if ".git" in path.parts or ".venv" in path.parts or RESULTS_DIR in path.parents:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(content) for pattern in patterns):
            findings.append(str(path.relative_to(BASE_DIR)))
    return findings


def is_env_ignored():
    gitignore = BASE_DIR / ".gitignore"
    return gitignore.exists() and ".env" in gitignore.read_text(encoding="utf-8").splitlines()


def inspect_permissions(paths):
    rows = []
    for path in paths:
        if path.exists():
            mode = path.stat().st_mode & 0o777
            rows.append({"archivo": path.name, "permisos": oct(mode), "lectura_otros": bool(mode & 0o004)})
    return rows


def build_risk_matrix(exposed, env_ignored, permissions):
    world_readable = any(item["lectura_otros"] for item in permissions)
    rows = [
        {
            "riesgo": "Exposición de datos financieros en CSV, SQLite o predicciones",
            "impacto": "Alto",
            "probabilidad": "Media",
            "nivel": "Alto",
            "evidencia": "El dataset contiene ingresos, score e historial de incumplimiento",
            "medida_propuesta": "Restringir accesos, cifrar respaldos y anonimizar antes de compartir",
        },
        {
            "riesgo": "Credenciales incluidas en el repositorio",
            "impacto": "Alto",
            "probabilidad": "Alta" if exposed else "Baja",
            "nivel": "Crítico" if exposed else "Medio",
            "evidencia": ", ".join(exposed) if exposed else "No se detectaron patrones básicos",
            "medida_propuesta": "Usar variables de entorno, rotar secretos y aplicar secret scanning",
        },
        {
            "riesgo": "Archivos de resultados legibles por otros usuarios del equipo",
            "impacto": "Medio",
            "probabilidad": "Media" if world_readable else "Baja",
            "nivel": "Medio",
            "evidencia": "Revisión de permisos locales: " + str(permissions),
            "medida_propuesta": "Aplicar permisos mínimos (600) y almacenamiento con control de acceso",
        },
        {
            "riesgo": "Sesgo o discriminación en decisiones crediticias automatizadas",
            "impacto": "Alto",
            "probabilidad": "Media",
            "nivel": "Alto",
            "evidencia": "El modelo procesa género, educación y variables socioeconómicas",
            "medida_propuesta": "Medir desempeño por grupos, revisión humana y documentar finalidad",
        },
        {
            "riesgo": "Acceso excesivo a datos y resultados",
            "impacto": "Alto",
            "probabilidad": "Media",
            "nivel": "Alto",
            "evidencia": "La demo local no implementa autenticación ni roles técnicos",
            "medida_propuesta": "Implementar RBAC con roles Data Engineer, Data Scientist, Auditor y BI",
        },
        {
            "riesgo": "Incumplimiento de retención y eliminación de datos",
            "impacto": "Alto",
            "probabilidad": "Media",
            "nivel": "Alto",
            "evidencia": "No existe política automática de retención en la demo",
            "medida_propuesta": "Definir finalidad, plazo de retención, borrado verificable y trazabilidad",
        },
    ]
    if not env_ignored:
        rows[1]["nivel"] = "Crítico"
        rows[1]["evidencia"] += "; .env no está excluido por Git"
    return pd.DataFrame(rows)


def build_report(df, exposed, env_exists, env_ignored, permissions, risks):
    sensitive_found = [f"- `{column}`: {category}" for column, category in SENSITIVE_COLUMNS.items() if column in df]
    role_table = """| Rol | Acceso recomendado |
|---|---|
| Data Engineer | Ingesta y datos seudonimizados; escritura del pipeline |
| Data Scientist | Datos validados necesarios y entrenamiento; sin credenciales de infraestructura |
| Analista BI | Métricas agregadas y predicciones autorizadas; solo lectura |
| Auditor/Seguridad | Logs, configuraciones y matriz de riesgos; sin modificar datos fuente |
| Administrador | Gestión de identidades, cifrado, respaldos y revocación de accesos |"""
    return f"""# Auditoría de seguridad del pipeline

## Alcance y resultado

- Archivo `.env` presente: **{'sí' if env_exists else 'no (no es necesario mientras no existan secretos locales)'}**.
- `.env` excluido por Git: **{'sí' if env_ignored else 'no'}**.
- Patrones básicos de credenciales expuestas: **{', '.join(exposed) if exposed else 'no detectados'}**.
- Archivos revisados en `resultados`: base SQLite, log y modelo entrenado.
- Permisos observados: `{permissions}`.

Esta revisión automática es una evidencia inicial; no reemplaza análisis de dependencias, infraestructura,
pruebas de penetración ni revisión legal profesional.

## Datos personales y financieros

No existen identificadores directos como nombre o RUT, pero la combinación de atributos puede permitir
perfilamiento o reidentificación. Se detectaron:

{chr(10).join(sensitive_found)}

## Roles y mínimo privilegio

{role_table}

## Normativa chilena

A la fecha de esta auditoría, la Ley N° 19.628 regula la protección de la vida privada. La Ley N° 21.719,
publicada el 13 de diciembre de 2024, perfecciona ese régimen y entra en vigencia el 1 de diciembre de 2026.
El proyecto debe anticipar finalidad y proporcionalidad del tratamiento, información a titulares, seguridad,
trazabilidad, atención de derechos, evaluación de proveedores y respuesta ante incidentes.

Fuentes oficiales:

- https://www.bcn.cl/leychile/navegar?idNorma=141599
- https://www.bcn.cl/leychile/navegar?i=1209272

## Matriz de riesgos

{markdown_table(risks)}

## Limitaciones y acciones prioritarias

1. La demo local no tiene autenticación: una integración real debe usar RBAC y cuentas nominativas.
2. Los archivos de predicciones no deben publicarse sin anonimización y autorización.
3. Deben probarse restauración de respaldos, rotación de secretos y respuesta a incidentes.
4. Antes de usar el modelo para decisiones reales se requiere evaluación de sesgo, explicabilidad y revisión humana.
"""


def markdown_table(dataframe):
    headers = dataframe.columns.tolist()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in dataframe.astype(str).itertuples(index=False, name=None):
        values = [value.replace("|", "/").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)

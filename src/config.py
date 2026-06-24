import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "raw" / "02_loan_data.csv"
METADATA_FILE = BASE_DIR / "data" / "raw" / "01_Metadata.txt"

RESULTS_DIR = BASE_DIR / "resultados"

# Subcarpetas de resultados organizadas por tipo de archivo.
DB_DIR = RESULTS_DIR / "db"            # bases de datos (.db)
CSV_DIR = RESULTS_DIR / "csv"          # tablas (.csv)
HTML_DIR = RESULTS_DIR / "html"        # dashboards e informe (.html)
CHARTS_DIR = RESULTS_DIR / "graficos"  # imágenes (.png)
EDA_CHARTS_DIR = CHARTS_DIR / "eda"    # gráficos del análisis exploratorio
JSON_DIR = RESULTS_DIR / "json"        # métricas en json (.json)
MODEL_DIR = RESULTS_DIR / "modelo"     # modelo serializado (.pkl)
LOG_DIR = RESULTS_DIR / "logs"         # registros de ejecución (.log)
REPORT_DIR = RESULTS_DIR / "reportes"  # reportes y guías (.md)

RESULT_DIRS = [DB_DIR, CSV_DIR, HTML_DIR, CHARTS_DIR, EDA_CHARTS_DIR, JSON_DIR, MODEL_DIR, LOG_DIR, REPORT_DIR]

# Caché de matplotlib fuera de resultados/ para no ensuciar la carpeta ordenada.
MPL_CACHE_DIR = BASE_DIR / ".matplotlib"

TABLE_NAME = "datos_validados"

# Archivos generados, cada uno en su subcarpeta según el tipo.
DATABASE_FILE = DB_DIR / "base_datos_validados.db"
ERROR_REPORT_FILE = CSV_DIR / "reporte_registros_con_errores.csv"
EDA_SUMMARY_FILE = CSV_DIR / "eda_resumen.csv"
MODEL_COMPARISON_FILE = CSV_DIR / "comparacion_modelos.csv"
PREDICTIONS_FILE = CSV_DIR / "predicciones_modelo.csv"
PERFORMANCE_METRICS_FILE = CSV_DIR / "performance_metrics.csv"
SECURITY_RISK_FILE = CSV_DIR / "security_risk_matrix.csv"
PRESENTATION_REPORT_FILE = HTML_DIR / "informe_presentacion.html"
CONFUSION_MATRIX_FILE = CHARTS_DIR / "matriz_confusion.png"
ROC_CURVE_FILE = CHARTS_DIR / "curva_roc.png"
MODEL_METRICS_FILE = JSON_DIR / "model_metrics.json"
MODEL_FILE = MODEL_DIR / "modelo_entrenado.pkl"
LOG_FILE = LOG_DIR / "pipeline.log"
SECURITY_REPORT_FILE = REPORT_DIR / "security_audit_report.md"
BI_GUIDE_FILE = REPORT_DIR / "guia_integracion_bi.md"


def ensure_result_dirs():
    """Crea todas las subcarpetas de resultados. Se llama al inicio del pipeline."""
    for directory in RESULT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)

EXECUTION_ENV = os.getenv("EXECUTION_ENV", "local")
PIPELINE_SAMPLE_SIZE = int(os.getenv("PIPELINE_SAMPLE_SIZE", "0")) or None
RANDOM_STATE = 42

REQUIRED_COLUMNS = [
    "person_age",
    "person_gender",
    "person_education",
    "person_income",
    "person_emp_exp",
    "person_home_ownership",
    "loan_amnt",
    "loan_intent",
    "loan_int_rate",
    "loan_percent_income",
    "cb_person_cred_hist_length",
    "credit_score",
    "previous_loan_defaults_on_file",
    "loan_status",
]

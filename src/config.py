import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "raw" / "02_loan_data.csv"
METADATA_FILE = BASE_DIR / "data" / "raw" / "01_Metadata.txt"
RESULTS_DIR = BASE_DIR / "resultados"
ERROR_REPORT_FILE = RESULTS_DIR / "reporte_registros_con_errores.csv"
DASHBOARD_FILE = RESULTS_DIR / "dashboard_calidad_datos.html"
DATABASE_FILE = RESULTS_DIR / "base_datos_validados.db"
LOG_FILE = RESULTS_DIR / "pipeline.log"
TABLE_NAME = "datos_validados"
EDA_SUMMARY_FILE = RESULTS_DIR / "eda_resumen.csv"
EDA_CHARTS_DIR = RESULTS_DIR / "graficos_eda"
MODEL_METRICS_FILE = RESULTS_DIR / "model_metrics.json"
MODEL_COMPARISON_FILE = RESULTS_DIR / "comparacion_modelos.csv"
MODEL_FILE = RESULTS_DIR / "modelo_entrenado.pkl"
PREDICTIONS_FILE = RESULTS_DIR / "predicciones_modelo.csv"
CONFUSION_MATRIX_FILE = RESULTS_DIR / "matriz_confusion.png"
ROC_CURVE_FILE = RESULTS_DIR / "curva_roc.png"
PERFORMANCE_METRICS_FILE = RESULTS_DIR / "performance_metrics.csv"
PERFORMANCE_REPORT_FILE = RESULTS_DIR / "performance_report.html"
SECURITY_REPORT_FILE = RESULTS_DIR / "security_audit_report.md"
SECURITY_RISK_FILE = RESULTS_DIR / "security_risk_matrix.csv"
FINAL_DASHBOARD_FILE = RESULTS_DIR / "dashboard_modelo_ia.html"
BI_GUIDE_FILE = RESULTS_DIR / "guia_integracion_bi.md"

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

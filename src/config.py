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

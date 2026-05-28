from charts import generate_charts
from config import DASHBOARD_FILE, DATABASE_FILE, ERROR_REPORT_FILE, LOG_FILE, RESULTS_DIR
from database import load_to_sqlite
from ingestion import ingest_data
from logger_config import setup_logger
from transform import clean_and_transform
from validation import validate_data


def main():
    logger = setup_logger()
    logger.info("Inicio del pipeline")

    try:
        raw_df = ingest_data(logger)
        clean_df = clean_and_transform(raw_df, logger)
        valid_df = validate_data(clean_df, logger)
        load_to_sqlite(valid_df, logger)
        generate_charts(len(clean_df), logger)

        logger.info("Fin del pipeline")
        print("\nPipeline ejecutado correctamente")
        print(f"Carpeta final de resultados: {RESULTS_DIR}")
        print(f"Base de datos: {DATABASE_FILE}")
        print(f"Archivo de logs: {LOG_FILE}")
        print(f"Reporte de errores: {ERROR_REPORT_FILE}")
        print(f"Dashboard HTML de KPIs: {DASHBOARD_FILE}")

    except Exception as error:
        logger.exception("Error durante la ejecución del pipeline: %s", error)
        print(f"\nError durante la ejecución del pipeline: {error}")
        raise


if __name__ == "__main__":
    main()

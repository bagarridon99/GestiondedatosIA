import pandas as pd

from bi_integration import write_bi_guide
from charts import generate_charts
from config import (
    DASHBOARD_FILE,
    DATABASE_FILE,
    ERROR_REPORT_FILE,
    FINAL_DASHBOARD_FILE,
    LOG_FILE,
    RESULTS_DIR,
)
from database import load_analysis_tables, load_to_sqlite
from eda_analysis import run_eda
from final_dashboard import generate_final_dashboard
from ingestion import ingest_data
from logger_config import setup_logger
from model_evaluation import evaluate_model
from model_training import train_models
from performance_monitor import PerformanceMonitor
from security_audit import run_security_audit
from transform import clean_and_transform
from validation import validate_data


def main():
    logger = setup_logger()
    monitor = PerformanceMonitor()
    logger.info("Inicio del pipeline")

    try:
        with monitor.measure("ingesta"):
            raw_df = ingest_data(logger)
        with monitor.measure("limpieza_transformacion"):
            clean_df = clean_and_transform(raw_df, logger)
        with monitor.measure("validacion"):
            valid_df = validate_data(clean_df, logger)
        with monitor.measure("carga_sqlite"):
            load_to_sqlite(valid_df, logger)
        with monitor.measure("dashboard_calidad"):
            generate_charts(len(clean_df), logger)
        with monitor.measure("eda"):
            run_eda(valid_df, logger)
        with monitor.measure("entrenamiento"):
            training_result = train_models(valid_df, logger)
        with monitor.measure("evaluacion"):
            metrics, predictions = evaluate_model(training_result, logger)
        with monitor.measure("seguridad"):
            risks = run_security_audit(valid_df, logger)

        performance = monitor.finalize(len(clean_df), logger)
        scalar_metrics = {key: value for key, value in metrics.items() if not isinstance(value, (list, dict))}
        load_analysis_tables(
            {
                "predicciones_modelo": predictions,
                "metricas_modelo": pd.DataFrame([scalar_metrics]),
                "comparacion_modelos": training_result["comparison"],
                "rendimiento_ultima_ejecucion": performance,
                "matriz_riesgos": risks,
            },
            logger,
        )
        write_bi_guide()
        generate_final_dashboard(
            len(clean_df),
            len(valid_df),
            metrics,
            training_result["comparison"],
            performance,
            risks,
            logger,
        )

        logger.info("Fin del pipeline")
        print("\nPipeline ejecutado correctamente")
        print(f"Carpeta final de resultados: {RESULTS_DIR}")
        print(f"Base de datos: {DATABASE_FILE}")
        print(f"Archivo de logs: {LOG_FILE}")
        print(f"Reporte de errores: {ERROR_REPORT_FILE}")
        print(f"Dashboard HTML de KPIs: {DASHBOARD_FILE}")
        print(f"Dashboard final del modelo: {FINAL_DASHBOARD_FILE}")

    except Exception as error:
        logger.exception("Error durante la ejecución del pipeline: %s", error)
        print(f"\nError durante la ejecución del pipeline: {error}")
        raise


if __name__ == "__main__":
    main()

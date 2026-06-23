import pandas as pd

from config import METADATA_FILE, PIPELINE_SAMPLE_SIZE, RAW_FILE


def ingest_data(logger):
    logger.info("Etapa 1: ingesta de datos")

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo requerido: {RAW_FILE}")

    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"No se encontró la metadata requerida: {METADATA_FILE}")

    df = pd.read_csv(RAW_FILE)
    if PIPELINE_SAMPLE_SIZE:
        df = df.head(PIPELINE_SAMPLE_SIZE).copy()
        logger.info("Muestra solicitada para comparación: %s registros", len(df))
    filas, columnas = df.shape
    logger.info("Metadata del caso encontrada en: %s", METADATA_FILE)
    logger.info("Datos ingestados: %s filas y %s columnas", filas, columnas)

    return df

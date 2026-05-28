import sqlite3

from config import DATABASE_FILE, TABLE_NAME


def load_to_sqlite(df, logger):
    logger.info("Etapa 4: carga a SQLite")

    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:
        df.to_sql(TABLE_NAME, connection, if_exists="replace", index=False)

    logger.info("Tabla %s creada o reemplazada", TABLE_NAME)
    logger.info("Registros cargados en SQLite: %s", len(df))
    logger.info("Base de datos guardada en: %s", DATABASE_FILE)

    return DATABASE_FILE

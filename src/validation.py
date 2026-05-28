from datetime import datetime

import pandas as pd

from config import ERROR_REPORT_FILE, REQUIRED_COLUMNS


def add_error(errors, row_index, field, value, rule, validation_date):
    errors.append(
        {
            "fila": row_index + 2,
            "campo": field,
            "valor_detectado": value,
            "regla_incumplida": rule,
            "fecha_validacion": validation_date,
        }
    )


def validate_data(df, logger):
    logger.info("Etapa 3: validación estructural y semántica")

    validation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    errors = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        for column in missing_columns:
            errors.append(
                {
                    "fila": 0,
                    "campo": column,
                    "valor_detectado": "columna inexistente",
                    "regla_incumplida": "La columna obligatoria debe existir",
                    "fecha_validacion": validation_date,
                }
            )
        save_error_report(errors)
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing_columns)}")

    for index, row in df.iterrows():
        validate_range(errors, index, row, "person_age", 18, 100, validation_date)
        validate_range(errors, index, row, "person_emp_exp", 0, 80, validation_date)
        validate_greater_than(errors, index, row, "person_income", 0, validation_date)
        validate_greater_than(errors, index, row, "loan_amnt", 0, validation_date)
        validate_greater_than(errors, index, row, "loan_int_rate", 0, validation_date)
        validate_range(errors, index, row, "loan_percent_income", 0, 1, validation_date)
        validate_greater_or_equal(errors, index, row, "cb_person_cred_hist_length", 0, validation_date)
        validate_range(errors, index, row, "credit_score", 300, 850, validation_date)
        validate_allowed_values(
            errors,
            index,
            row,
            "previous_loan_defaults_on_file",
            ["Yes", "No"],
            validation_date,
        )
        validate_allowed_values(errors, index, row, "loan_status", [0, 1], validation_date)

    error_rows = {error["fila"] for error in errors if error["fila"] > 0}
    valid_df = df[[index + 2 not in error_rows for index in df.index]]

    save_error_report(errors)

    logger.info("Registros válidos: %s", len(valid_df))
    logger.info("Errores detectados: %s", len(errors))
    logger.info("Reporte de errores guardado en: %s", ERROR_REPORT_FILE)

    return valid_df


def validate_range(errors, index, row, field, minimum, maximum, validation_date):
    value = row[field]
    if pd.isna(value) or value < minimum or value > maximum:
        add_error(errors, index, field, value, f"Debe estar entre {minimum} y {maximum}", validation_date)


def validate_greater_than(errors, index, row, field, minimum, validation_date):
    value = row[field]
    if pd.isna(value) or value <= minimum:
        add_error(errors, index, field, value, f"Debe ser mayor a {minimum}", validation_date)


def validate_greater_or_equal(errors, index, row, field, minimum, validation_date):
    value = row[field]
    if pd.isna(value) or value < minimum:
        add_error(errors, index, field, value, f"Debe ser mayor o igual a {minimum}", validation_date)


def validate_allowed_values(errors, index, row, field, allowed_values, validation_date):
    value = row[field]
    if value not in allowed_values:
        add_error(errors, index, field, value, f"Debe ser uno de: {allowed_values}", validation_date)


def save_error_report(errors):
    ERROR_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(
        errors,
        columns=["fila", "campo", "valor_detectado", "regla_incumplida", "fecha_validacion"],
    )
    report.to_csv(ERROR_REPORT_FILE, index=False)

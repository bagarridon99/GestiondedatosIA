import pandas as pd


def normalize_column_name(column_name):
    return column_name.strip().lower().replace(" ", "_")


def clean_and_transform(df, logger):
    logger.info("Etapa 2: limpieza y transformación")

    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]

    initial_rows = len(df)
    df = df.drop_duplicates()
    removed_duplicates = initial_rows - len(df)

    text_columns = df.select_dtypes(include=["object"]).columns
    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    numeric_columns = [
        "person_age",
        "person_income",
        "person_emp_exp",
        "loan_amnt",
        "loan_int_rate",
        "loan_percent_income",
        "cb_person_cred_hist_length",
        "credit_score",
        "loan_status",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["risk_income_level"] = pd.cut(
        df["person_income"],
        bins=[-float("inf"), 30000, 70000, float("inf")],
        labels=["bajo", "medio", "alto"],
    )
    df["loan_amount_level"] = pd.cut(
        df["loan_amnt"],
        bins=[-float("inf"), 5000, 15000, float("inf")],
        labels=["bajo", "medio", "alto"],
    )
    df["credit_score_level"] = pd.cut(
        df["credit_score"],
        bins=[-float("inf"), 579, 669, 739, float("inf")],
        labels=["bajo", "medio", "bueno", "excelente"],
    )

    logger.info("Duplicados eliminados: %s", removed_duplicates)
    logger.info("Datos limpios: %s filas y %s columnas", df.shape[0], df.shape[1])

    return df

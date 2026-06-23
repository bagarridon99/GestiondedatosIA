import time

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import MODEL_COMPARISON_FILE, MODEL_FILE, RANDOM_STATE


TARGET = "loan_status"
DERIVED_COLUMNS = ["risk_income_level", "loan_amount_level", "credit_score_level"]


def train_models(df, logger):
    logger.info("Etapa 7: entrenamiento y comparación de modelos")
    predictors = [column for column in df.columns if column not in [TARGET, *DERIVED_COLUMNS]]
    X = df[predictors].copy()
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    preprocessor = build_preprocessor(X)
    candidates = {
        "Regresión Logística": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            solver="liblinear",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=14,
            min_samples_leaf=2,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }

    fitted_models = {}
    comparison_rows = []
    for name, estimator in candidates.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
        start = time.perf_counter()
        pipeline.fit(X_train, y_train)
        elapsed = time.perf_counter() - start
        # Accelerate BLAS en algunas versiones de macOS emite warnings espurios
        # aun con matrices finitas; se valida explícitamente la salida.
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            prediction = pipeline.predict(X_test)
            probability = pipeline.predict_proba(X_test)[:, 1]
        if not np.isfinite(probability).all():
            raise ValueError(f"El modelo {name} generó probabilidades no finitas")
        comparison_rows.append(calculate_metrics(name, y_test, prediction, probability, elapsed))
        fitted_models[name] = pipeline
        logger.info("Modelo entrenado: %s (%.2f segundos)", name, elapsed)

    comparison = pd.DataFrame(comparison_rows).sort_values("auc", ascending=False).reset_index(drop=True)
    comparison["seleccionado"] = False
    comparison.loc[0, "seleccionado"] = True
    best_name = comparison.loc[0, "modelo"]
    best_model = fitted_models[best_name]
    comparison.to_csv(MODEL_COMPARISON_FILE, index=False)
    joblib.dump(best_model, MODEL_FILE)

    logger.info("Mejor modelo según AUC: %s", best_name)
    logger.info("Modelo guardado en: %s", MODEL_FILE)
    return {
        "model": best_model,
        "model_name": best_name,
        "X_test": X_test,
        "y_test": y_test,
        "comparison": comparison,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "predictors": predictors,
    }


def build_preprocessor(X):
    numeric_columns = X.select_dtypes(include="number").columns.tolist()
    categorical_columns = X.select_dtypes(exclude="number").columns.tolist()
    numeric_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric_pipeline, numeric_columns), ("categorical", categorical_pipeline, categorical_columns)]
    )


def calculate_metrics(name, y_true, prediction, probability, elapsed):
    auc = roc_auc_score(y_true, probability)
    return {
        "modelo": name,
        "accuracy": accuracy_score(y_true, prediction),
        "precision": precision_score(y_true, prediction, zero_division=0),
        "recall": recall_score(y_true, prediction, zero_division=0),
        "f1_score": f1_score(y_true, prediction, zero_division=0),
        "auc": auc,
        "gini": 2 * auc - 1,
        "tiempo_entrenamiento_segundos": elapsed,
    }

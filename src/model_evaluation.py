import json
import os

from config import (
    CONFUSION_MATRIX_FILE,
    MODEL_METRICS_FILE,
    MPL_CACHE_DIR,
    PREDICTIONS_FILE,
    ROC_CURVE_FILE,
)

os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

def evaluate_model(training_result, logger):
    logger.info("Etapa 8: evaluación del mejor modelo")
    model = training_result["model"]
    X_test = training_result["X_test"]
    y_test = training_result["y_test"]
    prediction = model.predict(X_test)
    probability = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, probability)
    matrix = confusion_matrix(y_test, prediction)

    metrics = {
        "modelo_seleccionado": training_result["model_name"],
        "criterio_seleccion": "Mayor AUC en el conjunto de prueba",
        "registros_entrenamiento": training_result["train_rows"],
        "registros_prueba": training_result["test_rows"],
        "variables_predictoras": training_result["predictors"],
        "accuracy": accuracy_score(y_test, prediction),
        "precision": precision_score(y_test, prediction, zero_division=0),
        "recall": recall_score(y_test, prediction, zero_division=0),
        "f1_score": f1_score(y_test, prediction, zero_division=0),
        "auc": auc,
        "gini": 2 * auc - 1,
        "matriz_confusion": matrix.tolist(),
        "interpretacion": (
            "En riesgo crediticio se prioriza detectar incumplimientos (recall), sin perder la capacidad "
            "global de discriminación medida por AUC y Gini."
        ),
    }
    MODEL_METRICS_FILE.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    predictions = X_test.copy()
    predictions.insert(0, "indice_original", X_test.index)
    predictions["loan_status_real"] = y_test.to_numpy()
    predictions["loan_status_predicho"] = prediction
    predictions["probabilidad_incumplimiento"] = probability
    predictions.to_csv(PREDICTIONS_FILE, index=False)

    plot_confusion_matrix(matrix, training_result["model_name"])
    plot_roc_curve(y_test, probability, auc)
    logger.info("Métricas del modelo guardadas en: %s", MODEL_METRICS_FILE)
    return metrics, predictions


def plot_confusion_matrix(matrix, model_name):
    display = ConfusionMatrixDisplay(matrix, display_labels=["Pagado", "Incumplido"])
    fig, ax = plt.subplots(figsize=(6, 5))
    display.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"Matriz de confusión - {model_name}")
    ax.set_xlabel("Etiqueta predicha")
    ax.set_ylabel("Etiqueta real")
    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_FILE, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_roc_curve(y_true, probability, auc):
    false_positive_rate, true_positive_rate, _ = roc_curve(y_true, probability)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(false_positive_rate, true_positive_rate, color="#1d4ed8", label=f"AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="#64748b", label="Clasificador aleatorio")
    ax.set(xlabel="Tasa de falsos positivos", ylabel="Tasa de verdaderos positivos", title="Curva ROC")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(ROC_CURVE_FILE, dpi=150, bbox_inches="tight")
    plt.close(fig)

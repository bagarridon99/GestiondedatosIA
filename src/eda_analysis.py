import os

from config import EDA_CHARTS_DIR, EDA_SUMMARY_FILE, MPL_CACHE_DIR

os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def run_eda(df, logger):
    logger.info("Etapa 6: análisis exploratorio de datos")
    EDA_CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    summary = build_summary(df)
    summary.to_csv(EDA_SUMMARY_FILE, index=False)
    plot_target_distribution(df)
    plot_numeric_distributions(df)
    plot_correlation_matrix(df)
    plot_bivariate_analysis(df)

    logger.info("Resumen EDA guardado en: %s", EDA_SUMMARY_FILE)
    logger.info("Gráficos EDA guardados en: %s", EDA_CHARTS_DIR)
    return summary


def build_summary(df):
    duplicate_count = int(df.duplicated().sum())
    rows = []
    for column in df.columns:
        series = df[column]
        mode = series.mode(dropna=True)
        row = {
            "variable": column,
            "tipo": str(series.dtype),
            "registros": len(series),
            "nulos": int(series.isna().sum()),
            "porcentaje_nulos": round(series.isna().mean() * 100, 4),
            "valores_unicos": int(series.nunique(dropna=True)),
            "moda": mode.iloc[0] if not mode.empty else None,
            "duplicados_dataset": duplicate_count,
        }
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            row.update(
                {
                    "media": clean.mean(),
                    "minimo": clean.min(),
                    "percentil_25": clean.quantile(0.25),
                    "mediana": clean.median(),
                    "percentil_75": clean.quantile(0.75),
                    "maximo": clean.max(),
                    "desviacion_estandar": clean.std(),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def plot_target_distribution(df):
    counts = df["loan_status"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(["Pagado (0)", "Incumplido (1)"], counts.values, color=["#2a9d8f", "#e76f51"])
    ax.set(title="Distribución de loan_status", ylabel="Registros")
    ax.bar_label(bars, labels=[f"{value:,}" for value in counts.values])
    save_figure(fig, "distribucion_loan_status.png")


def plot_numeric_distributions(df):
    columns = ["person_income", "loan_amnt", "loan_int_rate", "credit_score"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, column in zip(axes.flat, columns):
        ax.hist(df[column].dropna(), bins=30, color="#457b9d", alpha=0.85)
        ax.set_title(column)
        ax.set_ylabel("Frecuencia")
    fig.suptitle("Análisis univariado de variables numéricas", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "distribuciones_numericas.png")


def plot_correlation_matrix(df):
    numeric = df.select_dtypes(include="number")
    correlation = numeric.corr()
    fig, ax = plt.subplots(figsize=(11, 8))
    image = ax.imshow(correlation, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(correlation.columns)), correlation.columns, rotation=55, ha="right")
    ax.set_yticks(range(len(correlation.columns)), correlation.columns)
    fig.colorbar(image, ax=ax, label="Correlación de Pearson")
    ax.set_title("Matriz de correlación")
    fig.tight_layout()
    save_figure(fig, "matriz_correlacion.png")


def plot_bivariate_analysis(df):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    df.boxplot(column="loan_amnt", by="loan_status", ax=axes[0], grid=False)
    axes[0].set(title="Monto por estado del préstamo", xlabel="loan_status", ylabel="Monto")

    default_rate = df.groupby("loan_intent", observed=True)["loan_status"].mean().sort_values()
    default_rate.plot.barh(ax=axes[1], color="#f4a261")
    axes[1].set(title="Tasa de incumplimiento por propósito", xlabel="Proporción loan_status = 1")
    fig.suptitle("Análisis bivariado")
    fig.tight_layout()
    save_figure(fig, "analisis_bivariado.png")


def save_figure(fig, filename):
    fig.savefig(EDA_CHARTS_DIR / filename, dpi=140, bbox_inches="tight")
    plt.close(fig)

import base64
import html
import sqlite3
from pathlib import Path

import pandas as pd

from config import (
    CONFUSION_MATRIX_FILE,
    DATABASE_FILE,
    EDA_CHARTS_DIR,
    EDA_SUMMARY_FILE,
    PRESENTATION_REPORT_FILE,
    ROC_CURVE_FILE,
)

# Selección reducida de gráficos para la presentación. Cada elemento es
# (título, archivo, explicación corta). Edita esta lista si quieres mostrar
# otros gráficos de graficos_eda/ o cambiar las explicaciones.
EDA_CHARTS = [
    (
        "Distribución del estado del préstamo",
        "distribucion_loan_status.png",
        "Compara cuántos préstamos se pagaron (0) frente a los que se incumplieron (1). "
        "Permite ver si las clases están equilibradas o si una predomina.",
    ),
    (
        "Matriz de correlación",
        "matriz_correlacion.png",
        "Indica qué tan relacionadas están las variables. Rojo = suben juntas, "
        "azul = una sube y la otra baja, blanco = sin relación. La diagonal siempre vale 1.",
    ),
    (
        "Análisis bivariado",
        "analisis_bivariado.png",
        "Izquierda: el monto del préstamo según si se pagó o se incumplió. "
        "Derecha: qué propósitos de préstamo incumplen más (ordenados de mayor a menor).",
    ),
]

# Cuántas filas de muestra mostrar de las tablas de la base de datos.
SAMPLE_ROWS = 8

# Columnas (de las muchas que hay) que se muestran en cada muestra, para que
# las tablas no queden demasiado anchas.
DATA_SAMPLE_COLUMNS = [
    "person_age",
    "person_income",
    "loan_amnt",
    "loan_intent",
    "loan_int_rate",
    "credit_score",
    "loan_status",
]
PREDICTION_SAMPLE_COLUMNS = [
    "person_income",
    "loan_amnt",
    "credit_score",
    "loan_status_real",
    "loan_status_predicho",
    "probabilidad_incumplimiento",
]
PREDICTION_RENAME = {
    "loan_status_real": "Real",
    "loan_status_predicho": "Predicho",
    "probabilidad_incumplimiento": "Prob. incumplimiento",
}

# Iconos para los hallazgos de calidad de datos (verde / ámbar / azul).
INSIGHT_ICONS = {"ok": "✓", "warn": "!", "info": "•"}


def generate_presentation_report(total_rows, valid_rows, metrics, comparison, risks, logger):
    logger.info("Generación del informe resumido para presentación")
    rejected = total_rows - valid_rows

    quality_cards = "".join(
        [
            metric_card("Procesados", total_rows, integer=True),
            metric_card("Válidos", valid_rows, integer=True),
            metric_card("Rechazados", rejected, integer=True),
        ]
    )
    metric_cards = "".join(
        metric_card(label, metrics[key])
        for label, key in [
            ("Accuracy", "accuracy"),
            ("Precision", "precision"),
            ("Recall", "recall"),
            ("F1-score", "f1_score"),
            ("AUC", "auc"),
            ("Gini", "gini"),
        ]
    )

    eda_panels = "".join(
        f'<figure class="panel"><figcaption>{html.escape(title)}</figcaption>'
        f'<img src="{image_data_uri(EDA_CHARTS_DIR / filename)}" alt="{html.escape(title)}">'
        f'<p class="caption">{html.escape(description)}</p></figure>'
        for title, filename, description in EDA_CHARTS
        if (EDA_CHARTS_DIR / filename).exists()
    )
    eda_summary_html = read_eda_summary()
    eda_insights_html = read_eda_insights()
    model_insights_html = render_insights(build_model_insights(metrics))

    confusion_image = image_data_uri(CONFUSION_MATRIX_FILE)
    roc_image = image_data_uri(ROC_CURVE_FILE)
    comparison_html = dataframe_html(comparison.round(4))
    risks_html = dataframe_html(risks[["riesgo", "nivel", "medida_propuesta"]])

    db_tables_html, data_sample_html, predictions_sample_html = read_database_blocks(logger)

    report = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe resumido - Riesgo de préstamos</title>
<style>
:root{{--navy:#0f172a;--blue:#2563eb;--light:#f1f5f9;--line:#cbd5e1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--light);font-family:Arial,sans-serif;color:#1e293b}}
header{{background:linear-gradient(120deg,var(--navy),#1e3a8a);color:white;padding:32px max(5vw,24px)}}
header h1{{margin:0 0 6px}}header p{{margin:0;opacity:.9}}
main{{max-width:1100px;margin:auto;padding:24px}}
h2{{border-left:5px solid var(--blue);padding-left:10px;margin:34px 0 12px}}
h3{{margin:18px 0 8px;color:#334155}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:14px 0}}
.card,.panel{{background:white;border:1px solid var(--line);border-radius:10px;padding:18px}}
.value{{font-size:28px;font-weight:bold;color:#1d4ed8;margin-top:8px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
figure{{margin:0}}figcaption{{font-weight:bold;margin-bottom:10px}}
.caption{{margin:10px 0 0;color:#475569;font-size:14px;line-height:1.45}}
img{{max-width:100%;display:block;margin:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{border:1px solid #dbe3ec;padding:7px;text-align:left;white-space:nowrap}}th{{background:#e2e8f0}}
.scroll{{overflow:auto}}.note{{padding:12px;background:#eff6ff;border-left:4px solid var(--blue);margin-top:12px}}
.legend{{margin:0 0 14px;color:#475569;font-size:14px}}
.insights{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.insights li{{display:flex;gap:10px;align-items:flex-start;line-height:1.45;padding:10px 12px;border-radius:8px;background:#f8fafc;border:1px solid var(--line)}}
.ins-icon{{flex:0 0 22px;width:22px;height:22px;border-radius:50%;color:white;font-weight:bold;text-align:center;line-height:22px;font-size:13px}}
.ins-ok .ins-icon{{background:#16a34a}}.ins-warn .ins-icon{{background:#d97706}}.ins-info .ins-icon{{background:#2563eb}}
.print-btn{{position:fixed;top:16px;right:16px;border:0;border-radius:8px;padding:10px 16px;background:white;color:#1e3a8a;font-weight:bold;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.2)}}
@media(max-width:850px){{.grid{{grid-template-columns:1fr}}}}
@media print{{.print-btn{{display:none}}body{{background:white}}.panel,.card{{break-inside:avoid}}header{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">Imprimir / Guardar PDF</button>
<header><h1>Riesgo de incumplimiento de préstamos</h1>
<p>Informe resumido del pipeline DataOps: datos, exploración, modelo, base de datos y seguridad</p></header>
<main>
<h2>1. Calidad de los datos</h2><div class="cards">{quality_cards}</div>
<p class="note">De {total_rows:,} registros procesados, {valid_rows:,} pasaron las reglas de validación y {rejected:,} fueron rechazados.</p>

<h2>2. Exploración de datos (EDA)</h2><div class="grid">{eda_panels}</div>
<div class="panel" style="margin-top:18px"><h3>Lectura de los datos: ¿qué tan buenos son?</h3>{eda_insights_html}</div>
<div class="panel scroll" style="margin-top:18px"><h3>Estadísticas descriptivas (eda_resumen.csv)</h3>{eda_summary_html}</div>

<h2>3. Modelo: {html.escape(metrics['modelo_seleccionado'])}</h2><div class="cards">{metric_cards}</div>
<div class="panel" style="margin-top:18px"><h3>¿Qué significa este modelo?</h3>{model_insights_html}</div>
<div class="grid"><figure class="panel"><figcaption>Matriz de confusión</figcaption><img src="{confusion_image}" alt="Matriz de confusión">
<p class="caption">Compara lo real con lo predicho. La diagonal son los aciertos; fuera de ella, los errores. Lo ideal es que los números grandes queden en la diagonal.</p></figure>
<figure class="panel"><figcaption>Curva ROC</figcaption><img src="{roc_image}" alt="Curva ROC">
<p class="caption">Muestra el equilibrio entre detectar incumplimientos y las falsas alarmas. Mientras más se pega la curva a la esquina superior izquierda (AUC cercano a 1), mejor.</p></figure></div>
<div class="panel scroll" style="margin-top:18px"><h3>Comparación de modelos</h3>{comparison_html}</div>
<p class="note">Se eligió el modelo con mayor AUC en una partición de prueba estratificada (datos no vistos en el entrenamiento).</p>

<h2>4. Base de datos y predicciones</h2>
<div class="panel scroll"><h3>Tablas almacenadas en SQLite (base_datos_validados.db)</h3>
<p class="legend">Confirma que el pipeline guardó toda la información en la base de datos. Fíjate en que cada tabla tiene su número de filas (las de datos validados y predicciones son las más grandes).</p>{db_tables_html}</div>
<div class="panel scroll" style="margin-top:18px"><h3>Muestra de datos validados ({SAMPLE_ROWS} de {valid_rows:,} filas)</h3>
<p class="legend">Una muestra de los datos ya limpios y validados que quedaron en la base. Deberías ver registros completos y coherentes, sin celdas vacías ni valores raros.</p>{data_sample_html}</div>
<div class="panel scroll" style="margin-top:18px"><h3>Muestra de predicciones del modelo</h3>
<p class="legend">Compara la columna <em>Real</em> (lo que ocurrió) con <em>Predicho</em> (lo que estimó el modelo): cuando coinciden, acertó. <em>Prob. incumplimiento</em> va de 0 a 1; mientras más alta, más riesgo asignó el modelo.</p>{predictions_sample_html}</div>
<p class="note">Estos datos se leen directamente de la base de datos generada por el pipeline. La probabilidad de incumplimiento es la salida real del modelo para cada caso.</p>
<p class="note"><strong>Integración con BI:</strong> las 6 tablas de la base SQLite (datos validados, predicciones, métricas, comparación de modelos, rendimiento y matriz de riesgos) y los archivos CSV quedan listos para conectarse a Power BI o Metabase. La guía paso a paso está en <code>reportes/guia_integracion_bi.md</code>.</p>

<h2>5. Seguridad y riesgos</h2><div class="panel scroll">{risks_html}</div>
<p class="note">Los datos incluyen atributos personales y financieros. Requieren mínimo privilegio, cifrado, retención definida y revisión humana antes de usar las predicciones.</p>
</main></body></html>"""

    PRESENTATION_REPORT_FILE.write_text(report, encoding="utf-8")
    logger.info("Informe resumido guardado en: %s", PRESENTATION_REPORT_FILE)
    return PRESENTATION_REPORT_FILE


def read_eda_summary():
    """Tabla reducida de estadísticas descriptivas desde el CSV de EDA."""
    if not EDA_SUMMARY_FILE.exists():
        return "<p>No disponible.</p>"
    columns = ["variable", "nulos", "valores_unicos", "media", "mediana", "minimo", "maximo", "desviacion_estandar"]
    summary = pd.read_csv(EDA_SUMMARY_FILE)
    summary = summary[[c for c in columns if c in summary.columns]]
    return dataframe_html(summary.round(2).fillna(""))


def read_eda_insights():
    """Explicación en lenguaje simple de la calidad de los datos, derivada del CSV de EDA."""
    if not EDA_SUMMARY_FILE.exists():
        return ""
    summary = pd.read_csv(EDA_SUMMARY_FILE)
    legend = (
        '<p class="legend"><strong>Cómo leer la tabla de abajo:</strong> '
        "<em>nulos</em> = datos faltantes · <em>valores_unicos</em> = cuántos valores distintos hay · "
        "<em>media</em> y <em>mediana</em> = valor central · <em>mínimo/máximo</em> = rango · "
        "<em>desviacion_estandar</em> = qué tan dispersos están los datos.</p>"
    )
    return legend + render_insights(build_eda_insights(summary))


def render_insights(items):
    """Convierte una lista de (tipo, texto) en una lista HTML con iconos de color."""
    bullets = "".join(
        f'<li class="ins-{kind}"><span class="ins-icon">{INSIGHT_ICONS[kind]}</span> {html.escape(text)}</li>'
        for kind, text in items
    )
    return f'<ul class="insights">{bullets}</ul>'


def build_model_insights(metrics):
    """Explica en lenguaje simple el modelo y sus métricas, usando los valores reales."""
    insights = []
    name = metrics.get("modelo_seleccionado", "El modelo")
    insights.append((
        "info",
        f"{name} combina muchos 'árboles de decisión' y promedia sus votos; por eso suele ser "
        "preciso y robusto. Se eligió por tener el mayor AUC frente a la Regresión Logística.",
    ))
    if "accuracy" in metrics:
        insights.append(("ok", f"Acierta el {metrics['accuracy'] * 100:.0f}% de las predicciones sobre datos que no vio durante el entrenamiento."))
    if "recall" in metrics:
        insights.append(("ok", f"Detecta el {metrics['recall'] * 100:.0f}% de los incumplimientos reales. En riesgo de crédito esto es lo más importante: no dejar pasar a quien no pagará."))
    if "precision" in metrics:
        insights.append(("info", f"De cada 100 casos que marca como riesgosos, unos {metrics['precision'] * 100:.0f} realmente incumplen; el resto son falsas alarmas."))
    if "auc" in metrics:
        auc = float(metrics["auc"])
        nivel = "excelente" if auc >= 0.9 else "buena" if auc >= 0.8 else "aceptable"
        gini = metrics.get("gini")
        extra = f" (Gini {float(gini):.2f})" if gini is not None else ""
        insights.append(("info", f"AUC de {auc:.2f}{extra}: capacidad {nivel} para ordenar a las personas de mayor a menor riesgo."))
    cm = metrics.get("matriz_confusion")
    if cm and len(cm) == 2 and len(cm[0]) == 2:
        fp = int(cm[0][1])
        fn = int(cm[1][0])
        tp = int(cm[1][1])
        insights.append(("warn", f"En la prueba: detectó {tp:,} incumplimientos correctamente, se le escaparon {fn:,} (no los marcó) y marcó {fp:,} buenos pagadores como riesgosos por error."))
    return insights


def build_eda_insights(summary):
    """Genera hallazgos de calidad de datos a partir de las estadísticas (data-driven)."""
    insights = []
    n_vars = len(summary)

    if "nulos" in summary.columns:
        total_nulls = int(summary["nulos"].sum())
        if total_nulls == 0:
            insights.append(("ok", f"Datos completos: 0 valores nulos en las {n_vars} variables, no fue necesario rellenar faltantes."))
        else:
            worst = summary.loc[summary["nulos"].idxmax()]
            insights.append(("warn", f"Hay {total_nulls:,} valores faltantes; la variable con más es '{worst['variable']}' ({int(worst['nulos'])})."))

    if "duplicados_dataset" in summary.columns and len(summary):
        dups = int(summary["duplicados_dataset"].iloc[0])
        if dups == 0:
            insights.append(("ok", "Sin filas duplicadas: cada registro es único, no se contó dos veces a nadie."))
        else:
            insights.append(("warn", f"Se encontraron {dups:,} filas duplicadas que conviene revisar."))

    target = summary[summary["variable"] == "loan_status"]
    if not target.empty and pd.notna(target["media"].iloc[0]):
        rate = float(target["media"].iloc[0]) * 100
        balance = "balanceadas" if 40 <= rate <= 60 else "desbalanceadas"
        insights.append(("info", f"Balance de clases: {rate:.0f}% de los préstamos son incumplidos y {100 - rate:.0f}% pagados. Las clases están {balance}, algo clave al interpretar el modelo (por eso miramos recall y AUC, no solo accuracy)."))

    income = summary[summary["variable"] == "person_income"]
    if not income.empty and pd.notna(income["media"].iloc[0]) and pd.notna(income["mediana"].iloc[0]):
        media = float(income["media"].iloc[0])
        mediana = float(income["mediana"].iloc[0])
        if media > mediana * 1.1:
            insights.append(("info", f"El ingreso está sesgado: la media (${media:,.0f}) es mayor que la mediana (${mediana:,.0f}), o sea unos pocos ingresos muy altos estiran el promedio."))

    insights.append(("ok", "Todos estos registros ya pasaron las reglas de validación; los que tenían errores se separaron en 'reporte_registros_con_errores.csv'."))
    return insights


def read_database_blocks(logger):
    """Lee de la base de datos el resumen de tablas y dos muestras de filas."""
    if not DATABASE_FILE.exists():
        message = "<p>Base de datos no disponible.</p>"
        return message, message, message
    try:
        with sqlite3.connect(DATABASE_FILE) as con:
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()]
            overview = pd.DataFrame(
                {
                    "tabla": tables,
                    "filas": [con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables],
                }
            )
            data_sample = sample_table(con, "datos_validados", DATA_SAMPLE_COLUMNS)
            predictions_sample = sample_table(con, "predicciones_modelo", PREDICTION_SAMPLE_COLUMNS)
    except Exception as error:  # noqa: BLE001 - el informe no debe romper el pipeline
        logger.warning("No se pudo leer la base de datos para el informe: %s", error)
        message = "<p>No disponible.</p>"
        return message, message, message

    predictions_sample = predictions_sample.rename(columns=PREDICTION_RENAME)
    if "Prob. incumplimiento" in predictions_sample.columns:
        predictions_sample["Prob. incumplimiento"] = predictions_sample["Prob. incumplimiento"].round(3)

    return dataframe_html(overview), dataframe_html(data_sample), dataframe_html(predictions_sample)


def sample_table(con, table, columns, limit=SAMPLE_ROWS):
    available = [row[1] for row in con.execute(f'PRAGMA table_info("{table}")').fetchall()]
    selected = [c for c in columns if c in available] or available
    column_sql = ", ".join(f'"{c}"' for c in selected)
    return pd.read_sql(f'SELECT {column_sql} FROM "{table}" LIMIT {limit}', con)


def metric_card(label, value, integer=False):
    rendered = f"{int(value):,}" if integer else f"{float(value):.3f}"
    return f'<div class="card"><strong>{html.escape(label)}</strong><div class="value">{rendered}</div></div>'


def dataframe_html(dataframe):
    return dataframe.to_html(index=False, border=0, escape=True)


def image_data_uri(path):
    path = Path(path)
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

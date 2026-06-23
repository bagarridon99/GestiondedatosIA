import base64
import html
from pathlib import Path

import pandas as pd

from config import (
    CONFUSION_MATRIX_FILE,
    FINAL_DASHBOARD_FILE,
    ROC_CURVE_FILE,
)


def generate_final_dashboard(total_rows, valid_rows, metrics, comparison, performance, risks, logger):
    logger.info("Etapa 10: generación del dashboard final")
    rejected = total_rows - valid_rows
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
    quality_cards = "".join(
        [
            metric_card("Procesados", total_rows, integer=True),
            metric_card("Válidos", valid_rows, integer=True),
            metric_card("Rechazados", rejected, integer=True),
        ]
    )
    comparison_html = dataframe_html(comparison.round(4))
    performance_html = dataframe_html(performance.round(4))
    risks_html = dataframe_html(risks[["riesgo", "impacto", "probabilidad", "nivel", "medida_propuesta"]])
    confusion_image = image_data_uri(CONFUSION_MATRIX_FILE)
    roc_image = image_data_uri(ROC_CURVE_FILE)

    dashboard = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard IA - Riesgo de préstamos</title>
<style>
:root{{--navy:#0f172a;--blue:#2563eb;--light:#f1f5f9;--line:#cbd5e1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--light);font-family:Arial,sans-serif;color:#1e293b}}
header{{background:linear-gradient(120deg,var(--navy),#1e3a8a);color:white;padding:32px max(5vw,24px)}}
main{{max-width:1400px;margin:auto;padding:24px}}nav{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}}
button{{border:0;border-radius:7px;padding:10px 14px;background:#dbeafe;color:#1e3a8a;font-weight:bold;cursor:pointer}}
button.active{{background:var(--blue);color:white}}section{{display:none}}section.active{{display:block}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:18px 0}}
.card,.panel{{background:white;border:1px solid var(--line);border-radius:10px;padding:18px}}
.value{{font-size:30px;font-weight:bold;color:#1d4ed8;margin-top:8px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
img{{max-width:100%;display:block;margin:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{border:1px solid #dbe3ec;padding:8px;text-align:left}}th{{background:#e2e8f0}}
.scroll{{overflow:auto}}.note{{padding:14px;background:#eff6ff;border-left:4px solid var(--blue)}}
@media(max-width:850px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Riesgo de incumplimiento de préstamos</h1>
<p>Pipeline DataOps, calidad, modelo supervisado, rendimiento y seguridad</p></header>
<main><nav>
<button class="active" data-tab="resumen">Resumen</button><button data-tab="modelo">Modelo</button>
<button data-tab="rendimiento">Rendimiento</button><button data-tab="seguridad">Seguridad</button>
</nav>
<section id="resumen" class="active"><h2>Calidad de datos</h2><div class="cards">{quality_cards}</div>
<h2>Modelo seleccionado: {html.escape(metrics['modelo_seleccionado'])}</h2><div class="cards">{metric_cards}</div>
<p class="note">Selección: mayor AUC en prueba estratificada. La evaluación usa datos no vistos durante el entrenamiento.</p></section>
<section id="modelo"><div class="grid"><div class="panel"><h2>Matriz de confusión</h2><img src="{confusion_image}" alt="Matriz de confusión"></div>
<div class="panel"><h2>Curva ROC</h2><img src="{roc_image}" alt="Curva ROC"></div></div>
<div class="panel scroll"><h2>Comparación de modelos</h2>{comparison_html}</div></section>
<section id="rendimiento"><div class="panel scroll"><h2>Última ejecución por etapa</h2>{performance_html}</div>
<p class="note">Las mediciones son del proceso Python. El archivo performance_metrics.csv conserva el historial para comparar volúmenes o entornos.</p></section>
<section id="seguridad"><div class="panel scroll"><h2>Matriz de riesgos</h2>{risks_html}</div>
<p class="note">No hay identificadores directos, pero sí atributos personales y financieros. Se requiere mínimo privilegio, cifrado, retención definida y revisión humana.</p></section>
</main><script>
document.querySelectorAll('button[data-tab]').forEach(button=>button.addEventListener('click',()=>{{
 document.querySelectorAll('button[data-tab],section').forEach(element=>element.classList.remove('active'));
 button.classList.add('active');document.getElementById(button.dataset.tab).classList.add('active');
}}));
</script></body></html>"""
    FINAL_DASHBOARD_FILE.write_text(dashboard, encoding="utf-8")
    logger.info("Dashboard final guardado en: %s", FINAL_DASHBOARD_FILE)
    return FINAL_DASHBOARD_FILE


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

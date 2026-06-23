# Sistema DataOps para riesgo de préstamos

Pipeline académico de Gestión de Datos para IA (ITY1101). Procesa datos crediticios, controla su calidad,
entrena modelos de clasificación para predecir `loan_status`, evalúa rendimiento y seguridad, y publica
resultados para dashboard e integración BI.

## Flujo completo

1. **Ingesta:** lee el CSV y verifica su metadata.
2. **Limpieza:** normaliza columnas, tipos y categorías; elimina duplicados.
3. **Validación:** aplica reglas estructurales y semánticas y separa registros rechazados.
4. **Carga:** guarda los registros válidos en SQLite.
5. **EDA:** calcula media, moda, percentiles, nulos, duplicados y análisis uni/bivariado.
6. **Entrenamiento:** divide 80/20 con estratificación y aplica preprocesamiento mediante `ColumnTransformer`.
7. **Comparación:** entrena Regresión Logística y Random Forest y selecciona el mayor AUC.
8. **Evaluación:** genera accuracy, precision, recall, F1, matriz de confusión, ROC, AUC y Gini.
9. **Rendimiento:** mide tiempo, CPU, memoria y errores por etapa; conserva historial de ejecuciones.
10. **Seguridad:** revisa secretos, permisos, datos sensibles, roles y riesgos.
11. **Visualización/BI:** genera un dashboard HTML y tablas listas para Power BI o Metabase.

## Ejecución

Desde la raíz del repositorio:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

En Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```

El pipeline también se puede ejecutar con Docker:

```bash
docker build -t pipeline-prestamos .
docker run --rm -v "$(pwd)/resultados:/app/resultados" pipeline-prestamos
```

## Comparación de rendimiento

`performance_metrics.csv` acumula ejecuciones identificadas por entorno y volumen. Por ejemplo:

```bash
PIPELINE_SAMPLE_SIZE=10000 EXECUTION_ENV=local_10k python src/main.py
EXECUTION_ENV=local_45k python src/main.py
```

Para comparar local con Docker o nube, usa un nombre distinto en `EXECUTION_ENV` y conserva la misma
carpeta `resultados`. Las mediciones de nube deben provenir de una ejecución real; el proyecto no las simula.

## Archivos generados

Todos quedan en `resultados/`:

| Archivo | Contenido |
|---|---|
| `base_datos_validados.db` | Datos válidos y tablas de análisis para BI |
| `reporte_registros_con_errores.csv` | Reglas incumplidas por los registros rechazados |
| `dashboard_calidad_datos.html` | KPIs de calidad de la fase anterior |
| `eda_resumen.csv` | Estadísticas descriptivas, nulos y duplicados |
| `graficos_eda/` | Distribuciones, correlación y análisis bivariado |
| `comparacion_modelos.csv` | Comparación de los dos algoritmos |
| `model_metrics.json` | Métricas e interpretación del modelo seleccionado |
| `modelo_entrenado.pkl` | Pipeline de preprocesamiento y modelo serializado |
| `predicciones_modelo.csv` | Resultado real, predicción y probabilidad |
| `matriz_confusion.png` | Aciertos y errores por clase |
| `curva_roc.png` | Sensibilidad frente a falsos positivos |
| `performance_metrics.csv` | Historial de tiempo, CPU, RAM y errores |
| `performance_report.html` | Comparación visual de rendimiento |
| `security_audit_report.md` | Auditoría, roles, normativa y limitaciones |
| `security_risk_matrix.csv` | Riesgos, impacto, probabilidad y mitigación |
| `dashboard_modelo_ia.html` | Dashboard integrado e interactivo |
| `guia_integracion_bi.md` | Pasos y tablas para Power BI o Metabase |

## Interpretación de métricas

- **Accuracy:** proporción total de predicciones correctas; puede ocultar problemas si las clases están desbalanceadas.
- **Precision:** de los casos predichos como incumplimiento, cuántos realmente incumplieron.
- **Recall:** de los incumplimientos reales, cuántos detectó el modelo. Es especialmente relevante para riesgo.
- **F1-score:** equilibrio entre precision y recall.
- **AUC:** capacidad de ordenar casos de mayor a menor riesgo en distintos umbrales.
- **Gini:** transformación de AUC (`2 × AUC - 1`); valores mayores indican mejor discriminación.
- **Matriz de confusión:** muestra verdaderos/falsos positivos y negativos.

## Integración BI y seguridad

El dashboard HTML permite una demo local inmediata. Para evidencia de integración organizacional, SQLite
expone `datos_validados`, `predicciones_modelo`, `metricas_modelo`, `comparacion_modelos`,
`rendimiento_ultima_ejecucion` y `matriz_riesgos`. Consulta `resultados/guia_integracion_bi.md`.

Los datos incluyen atributos personales indirectos y financieros. No deben publicarse las predicciones
detalladas sin autorización, control de acceso, propósito definido, retención limitada y revisión de sesgo.

## Limitaciones y mejoras propuestas

- El dataset es una muestra académica sin dimensión temporal; falta validación externa y monitoreo de deriva.
- La comparación usa una sola partición estratificada. Como mejora se propone validación cruzada y ajuste de hiperparámetros.
- AUC alto no garantiza probabilidades calibradas ni decisiones justas. Se debe evaluar calibración, sesgo por grupos y explicabilidad.
- El dashboard HTML facilita la demo, pero no implementa autenticación. En producción debe publicarse en BI con RBAC.
- El historial incluye mediciones locales de 10.000 y 45.000 registros. Una comparación con nube requiere ejecutar allí el pipeline.
- SQLite es adecuado para la demo; PostgreSQL administrado permitiría concurrencia, respaldos y controles de acceso más robustos.

## Estructura

```text
data/raw/          Datos y metadata de entrada
src/               Módulos del pipeline
resultados/        Evidencias generadas (excluidas de Git)
Dockerfile         Entorno reproducible Python 3.11
requirements.txt   Dependencias
```

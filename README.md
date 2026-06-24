# Sistema DataOps para riesgo de préstamos

Pipeline académico de Gestión de Datos para IA (ITY1101). Procesa datos crediticios, controla su calidad,
entrena modelos de clasificación para predecir `loan_status`, evalúa rendimiento y seguridad, y publica
los resultados en un informe HTML resumido y tablas listas para integración BI.

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
11. **Informe/BI:** genera un informe HTML resumido y tablas listas para Power BI o Metabase.

## Ejecución

### Forma simple (recomendada)

Un solo comando, sin activar el entorno ni recordar variables. La primera vez crea el entorno e
instala las dependencias automáticamente.

En Mac/Linux:

```bash
./run.sh          # dataset completo
./run.sh 5000     # muestra de 5000 registros (más rápido)
```

En Windows (doble clic en `run.bat`, o desde la terminal):

```bat
run.bat
run.bat 5000
```

Funciona desde cualquier carpeta usando la ruta completa al script.

### Forma manual

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

`csv/performance_metrics.csv` acumula ejecuciones identificadas por entorno y volumen. Por ejemplo:

```bash
PIPELINE_SAMPLE_SIZE=10000 EXECUTION_ENV=local_10k python src/main.py
EXECUTION_ENV=local_45k python src/main.py
```

Para comparar local con Docker o nube, usa un nombre distinto en `EXECUTION_ENV` y conserva la misma
carpeta `resultados`. Las mediciones de nube deben provenir de una ejecución real; el proyecto no las simula.

## Archivos generados

Quedan en `resultados/`, organizados por tipo en subcarpetas. El archivo principal es
`html/informe_presentacion.html`.

| Archivo | Contenido |
|---|---|
| `html/informe_presentacion.html` | **Informe principal:** gráficos, métricas y muestras de datos en una sola página |
| `db/base_datos_validados.db` | Datos válidos y tablas de análisis para BI |
| `csv/reporte_registros_con_errores.csv` | Reglas incumplidas por los registros rechazados |
| `csv/eda_resumen.csv` | Estadísticas descriptivas, nulos y duplicados |
| `csv/comparacion_modelos.csv` | Comparación de los dos algoritmos |
| `csv/predicciones_modelo.csv` | Resultado real, predicción y probabilidad |
| `csv/performance_metrics.csv` | Historial de tiempo, CPU, RAM y errores |
| `csv/security_risk_matrix.csv` | Riesgos, impacto, probabilidad y mitigación |
| `graficos/eda/` | Distribuciones, correlación y análisis bivariado |
| `graficos/matriz_confusion.png` | Aciertos y errores por clase |
| `graficos/curva_roc.png` | Sensibilidad frente a falsos positivos |
| `json/model_metrics.json` | Métricas e interpretación del modelo seleccionado |
| `modelo/modelo_entrenado.pkl` | Pipeline de preprocesamiento y modelo serializado |
| `reportes/security_audit_report.md` | Auditoría, roles, normativa y limitaciones |
| `reportes/guia_integracion_bi.md` | Pasos y tablas para Power BI o Metabase |
| `logs/pipeline.log` | Registro completo de la ejecución |

## Interpretación de métricas

- **Accuracy:** proporción total de predicciones correctas; puede ocultar problemas si las clases están desbalanceadas.
- **Precision:** de los casos predichos como incumplimiento, cuántos realmente incumplieron.
- **Recall:** de los incumplimientos reales, cuántos detectó el modelo. Es especialmente relevante para riesgo.
- **F1-score:** equilibrio entre precision y recall.
- **AUC:** capacidad de ordenar casos de mayor a menor riesgo en distintos umbrales.
- **Gini:** transformación de AUC (`2 × AUC - 1`); valores mayores indican mejor discriminación.
- **Matriz de confusión:** muestra verdaderos/falsos positivos y negativos.

## Integración BI y seguridad

El informe HTML (`html/informe_presentacion.html`) permite una demo local inmediata. Para evidencia de
integración organizacional, SQLite expone `datos_validados`, `predicciones_modelo`, `metricas_modelo`,
`comparacion_modelos`, `rendimiento_ultima_ejecucion` y `matriz_riesgos`. Consulta
`resultados/reportes/guia_integracion_bi.md`.

Los datos incluyen atributos personales indirectos y financieros. No deben publicarse las predicciones
detalladas sin autorización, control de acceso, propósito definido, retención limitada y revisión de sesgo.

## Limitaciones y mejoras propuestas

- El dataset es una muestra académica sin dimensión temporal; falta validación externa y monitoreo de deriva.
- La comparación usa una sola partición estratificada. Como mejora se propone validación cruzada y ajuste de hiperparámetros.
- AUC alto no garantiza probabilidades calibradas ni decisiones justas. Se debe evaluar calibración, sesgo por grupos y explicabilidad.
- El informe HTML facilita la demo, pero no implementa autenticación. En producción debe publicarse en BI con RBAC.
- El historial incluye mediciones locales de 10.000 y 45.000 registros. Una comparación con nube requiere ejecutar allí el pipeline.
- SQLite es adecuado para la demo; PostgreSQL administrado permitiría concurrencia, respaldos y controles de acceso más robustos.

## Estructura

```text
data/raw/          Datos y metadata de entrada
src/               Módulos del pipeline
resultados/        Evidencias generadas en subcarpetas por tipo
                   (db, csv, html, graficos, json, modelo, reportes, logs); excluidas de Git
run.sh / run.bat   Ejecutan el pipeline (Mac/Linux y Windows)
Dockerfile         Entorno reproducible Python 3.11
requirements.txt   Dependencias
```

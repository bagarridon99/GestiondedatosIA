from config import BI_GUIDE_FILE, DATABASE_FILE, PERFORMANCE_METRICS_FILE, PREDICTIONS_FILE


def write_bi_guide():
    guide = f"""# Guía de integración con Power BI o Metabase

## Fuente recomendada

El pipeline actualiza automáticamente `{DATABASE_FILE.name}`. Las tablas disponibles son:

- `datos_validados`: datos que superaron las reglas de calidad.
- `predicciones_modelo`: prueba, predicción y probabilidad de incumplimiento.
- `metricas_modelo`: métricas del modelo seleccionado.
- `comparacion_modelos`: comparación de Regresión Logística y Random Forest.
- `rendimiento_ultima_ejecucion`: tiempo, CPU, memoria y errores por etapa.
- `matriz_riesgos`: hallazgos y medidas de seguridad.

También se pueden importar directamente `{PREDICTIONS_FILE.name}` y
`{PERFORMANCE_METRICS_FILE.name}` como archivos CSV.

## Flujo en Power BI Desktop

1. Instalar un controlador SQLite compatible o importar los CSV desde **Obtener datos > Texto/CSV**.
2. Relacionar predicciones con `datos_validados` mediante `indice_original` si se necesita detalle.
3. Crear tarjetas para accuracy, precision, recall, F1, AUC y Gini.
4. Agregar matriz de confusión, curva ROC, distribución de `loan_status` y comparación de modelos.
5. Actualizar las fuentes después de ejecutar `python src/main.py`.

## Seguridad

Publicar solo métricas agregadas. El detalle financiero requiere espacio de trabajo restringido, acceso de
solo lectura para analistas BI y una política de actualización/retención documentada.
"""
    BI_GUIDE_FILE.write_text(guide, encoding="utf-8")
    return BI_GUIDE_FILE

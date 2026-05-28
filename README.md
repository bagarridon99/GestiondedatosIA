# Pipeline de datos de préstamos

Este proyecto ejecuta un pipeline simple en Python para limpiar, validar y cargar datos de préstamos en una base SQLite. Al finalizar genera una carpeta `resultados/` con la base de datos, un dashboard HTML de KPIs, un reporte de errores y logs de ejecución.

## Estructura del proyecto

- `data/raw`: archivos originales del caso.
- `src`: código Python del pipeline.
- `resultados`: carpeta generada automáticamente con las evidencias finales.
- `Dockerfile`: permite ejecutar el proyecto con Docker.
- `run_windows.ps1`: script para correr Docker fácilmente en Windows PowerShell.

Archivos de entrada requeridos:

```text
data/raw/01_Metadata.txt
data/raw/02_loan_data.csv
```

## Cómo ejecutar con Python

Instala dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta el pipeline desde la carpeta `Pipeline`:

```bash
python src/main.py
```

En Mac puede ser necesario:

```bash
python3 src/main.py
```

## Cómo ejecutar con Docker en Windows

Requisitos:

- Tener Docker Desktop instalado.
- Tener Docker Desktop abierto.
- Estar ubicado en la carpeta `Pipeline`.

Forma recomendada con PowerShell:

```powershell
.\run_windows.ps1
```

Si PowerShell bloquea el script, ejecuta:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_windows.ps1
```

También puedes ejecutar Docker manualmente:

```powershell
docker build -t pipeline-prestamos .
docker run --rm -v "${PWD}/resultados:/app/resultados" pipeline-prestamos
```

## Cómo abrir PowerShell en la carpeta correcta

Opción 1:

1. Abre la carpeta `Pipeline` en el Explorador de archivos.
2. Haz clic en la barra de dirección.
3. Escribe `powershell`.
4. Presiona Enter.

Opción 2 desde VS Code:

1. Abre la carpeta `Pipeline` en VS Code.
2. Ve a `Terminal > New Terminal`.
3. Ejecuta el comando correspondiente.

Para confirmar que estás en la carpeta correcta:

```powershell
dir
```

Deberías ver archivos como:

```text
Dockerfile
README.md
requirements.txt
run_windows.ps1
src
data
resultados
```

## Qué archivos se generan

Después de ejecutar `main.py`, se crea o actualiza:

```text
resultados/base_datos_validados.db
resultados/dashboard_calidad_datos.html
resultados/reporte_registros_con_errores.csv
resultados/pipeline.log
```

Qué significa cada archivo:

- `base_datos_validados.db`: base SQLite con la tabla `datos_validados`.
- `dashboard_calidad_datos.html`: dashboard visual con KPIs de calidad.
- `reporte_registros_con_errores.csv`: registros rechazados y motivo del error.
- `pipeline.log`: registro de las etapas ejecutadas.

## Cómo ver los KPIs

Abre este archivo en el navegador:

```text
resultados/dashboard_calidad_datos.html
```

El dashboard muestra:

- Registros procesados.
- Porcentaje de registros válidos.
- Porcentaje de registros con errores.
- Porcentaje de registros con warnings.
- Warnings detectados.
- Errores por campo.
- Ejemplos de registros válidos, con warnings y con errores.

## Extensiones recomendadas para VS Code

Para revisar mejor los archivos generados, se recomienda instalar estas extensiones:

- `SQLite Viewer` de Florian Klampfer: permite abrir y revisar visualmente la base `base_datos_validados.db`.
- `Excel Viewer`: permite ver archivos `.csv` en formato de tabla.
- `Rainbow CSV`: ayuda a leer archivos `.csv` separando columnas por colores.

Estas extensiones son opcionales, pero facilitan revisar la base de datos y los reportes desde VS Code.

## Cómo ver la base de datos en VS Code

Puedes abrir:

```text
resultados/base_datos_validados.db
```

Con la extensión SQLite Viewer puedes revisar la tabla visualmente.

La tabla principal se llama:

```text
datos_validados
```

## Consultas SQL de ejemplo

Desde terminal:

```bash
sqlite3 resultados/base_datos_validados.db
```

Luego puedes ejecutar:

```sql
.tables
```

Total de registros cargados:

```sql
SELECT COUNT(*) AS total_registros
FROM datos_validados;
```

Distribución de estado del préstamo:

```sql
SELECT loan_status, COUNT(*) AS cantidad
FROM datos_validados
GROUP BY loan_status;
```

Promedio de credit score por estado:

```sql
SELECT loan_status, ROUND(AVG(credit_score), 2) AS promedio_credit_score
FROM datos_validados
GROUP BY loan_status;
```

Promedio de monto del préstamo por estado:

```sql
SELECT loan_status, ROUND(AVG(loan_amnt), 2) AS promedio_monto
FROM datos_validados
GROUP BY loan_status;
```

Primeros 10 registros:

```sql
SELECT *
FROM datos_validados
LIMIT 10;
```

Para salir de SQLite:

```sql
.exit
```

## Resumen del flujo

1. Lee los archivos originales desde `data/raw`.
2. Limpia y transforma los datos con pandas.
3. Valida reglas estructurales y semánticas.
4. Carga solo registros válidos a SQLite.
5. Genera dashboard HTML de KPIs.
6. Guarda evidencias finales en `resultados/`.

@echo off
REM ============================================================
REM  COMO CORRER EL PIPELINE  (Windows)
REM ============================================================
REM  Ejecuta el pipeline sin activar el entorno ni recordar variables.
REM
REM   run.bat          -> ejecuta con el dataset completo
REM   run.bat 5000     -> ejecuta con una muestra de 5000 registros (mas rapido)
REM
REM  Tambien puedes hacer doble clic en este archivo.
REM
REM  Al terminar, abre el informe en el navegador con:
REM   start resultados\informe_presentacion.html
REM
REM  En Mac/Linux usa el equivalente: run.sh
REM ============================================================

REM Ir siempre a la carpeta de este script, sin importar desde donde se ejecute.
cd /d "%~dp0"

REM La primera vez (o si no existe el entorno) lo crea e instala dependencias.
if not exist ".venv\Scripts\python.exe" (
  echo Primera ejecucion: creando entorno virtual e instalando dependencias...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install --quiet --upgrade pip
  .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
)

REM Si pasas un numero como argumento, se usa como tamano de muestra.
if not "%~1"=="" set PIPELINE_SAMPLE_SIZE=%~1

REM Ejecuta el pipeline con el Python del entorno (no hace falta activarlo).
.venv\Scripts\python.exe src\main.py

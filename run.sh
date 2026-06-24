#!/usr/bin/env bash
# ============================================================
#  CÓMO CORRER EL PIPELINE  (Mac / Linux)
# ============================================================
#  Ejecuta el pipeline sin activar el entorno ni recordar variables.
#
#   ./run.sh          -> ejecuta con el dataset completo
#   ./run.sh 5000     -> ejecuta con una muestra de 5000 registros (más rápido)
#
#  Funciona desde cualquier carpeta usando la ruta completa, por ejemplo:
#   ~/Documents/Proyectos/GestiondedatosIA/run.sh
#
#  Al terminar, abre el informe en el navegador con:
#   open resultados/informe_presentacion.html
#
#  En Windows usa el equivalente: run.bat
# ============================================================
set -e

# Ir siempre a la carpeta del proyecto, sin importar desde dónde se ejecute.
cd "$(dirname "$0")"

# La primera vez (o si no existe el entorno) lo crea e instala dependencias.
if [ ! -x ".venv/bin/python" ]; then
  echo "Primera ejecución: creando entorno virtual e instalando dependencias..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements.txt
fi

# Si pasas un número como argumento, se usa como tamaño de muestra.
if [ -n "$1" ]; then
  export PIPELINE_SAMPLE_SIZE="$1"
fi

# Ejecuta el pipeline con el Python del entorno (no hace falta activarlo).
.venv/bin/python src/main.py

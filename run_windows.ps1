$ErrorActionPreference = "Stop"

Write-Host "Construyendo imagen Docker..."
docker build -t pipeline-prestamos .

Write-Host "Ejecutando pipeline con carpeta resultados montada..."
docker run --rm -v "${PWD}/resultados:/app/resultados" pipeline-prestamos

Write-Host ""
Write-Host "Pipeline finalizado."
Write-Host "Revisa los archivos generados en la carpeta resultados."

import os
import platform
import time
import uuid
from contextlib import contextmanager
from datetime import datetime

import pandas as pd
import psutil

from config import EXECUTION_ENV, LOG_FILE, PERFORMANCE_METRICS_FILE, PERFORMANCE_REPORT_FILE


class PerformanceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.started_at = time.perf_counter()
        self.started_cpu = self._cpu_seconds()
        self.rows = []
        self.dataset_rows = 0

    @contextmanager
    def measure(self, stage):
        start = time.perf_counter()
        start_cpu = self._cpu_seconds()
        start_memory = self._memory_mb()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            cpu_delta = self._cpu_seconds() - start_cpu
            self.rows.append(
                self._row(
                    stage,
                    elapsed,
                    (cpu_delta / elapsed * 100) if elapsed else 0,
                    max(start_memory, self._memory_mb()),
                )
            )

    def finalize(self, dataset_rows, logger):
        self.dataset_rows = dataset_rows
        total_time = time.perf_counter() - self.started_at
        cpu_delta = self._cpu_seconds() - self.started_cpu
        for row in self.rows:
            row["registros_procesados"] = dataset_rows
        self.rows.append(
            self._row(
                "pipeline_total",
                total_time,
                (cpu_delta / total_time * 100) if total_time else 0,
                self._memory_mb(),
            )
        )
        current = pd.DataFrame(self.rows)
        history = self._load_history()
        combined = pd.concat([history, current], ignore_index=True)
        combined.to_csv(PERFORMANCE_METRICS_FILE, index=False)
        self._write_report(combined)
        logger.info("Métricas de rendimiento guardadas en: %s", PERFORMANCE_METRICS_FILE)
        return current

    def _row(self, stage, seconds, cpu_percent, memory_mb):
        return {
            "run_id": self.run_id,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "entorno": EXECUTION_ENV,
            "sistema": platform.system(),
            "python": platform.python_version(),
            "registros_procesados": self.dataset_rows,
            "etapa": stage,
            "tiempo_segundos": round(seconds, 4),
            "cpu_porcentaje_proceso": round(cpu_percent, 2),
            "memoria_mb": round(memory_mb, 2),
            "errores_log": count_log_errors(),
        }

    def _load_history(self):
        if not PERFORMANCE_METRICS_FILE.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(PERFORMANCE_METRICS_FILE)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame()

    def _write_report(self, history):
        totals = history[history["etapa"] == "pipeline_total"].copy()
        latest = history[history["run_id"] == self.run_id]
        comparison = totals.tail(10).to_html(index=False, classes="table", border=0)
        stages = latest.to_html(index=False, classes="table", border=0)
        report = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Rendimiento del pipeline</title>
<style>body{{font-family:Arial;max-width:1200px;margin:32px auto;color:#1f2937}}
.table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:8px;border:1px solid #d1d5db}}
th{{background:#e5e7eb}}.note{{background:#eff6ff;padding:14px;border-left:4px solid #2563eb}}</style></head>
<body><h1>Análisis de rendimiento</h1>
<p class="note">CPU corresponde al proceso Python y la memoria es RSS. El historial permite comparar
volúmenes o entornos sin inventar mediciones de nube.</p>
<h2>Última ejecución por etapa</h2>{stages}
<h2>Comparación de ejecuciones</h2>{comparison}
<p>Para comparar: <code>PIPELINE_SAMPLE_SIZE=10000 EXECUTION_ENV=local_10k python src/main.py</code></p>
</body></html>"""
        PERFORMANCE_REPORT_FILE.write_text(report, encoding="utf-8")

    def _cpu_seconds(self):
        cpu = self.process.cpu_times()
        return cpu.user + cpu.system

    def _memory_mb(self):
        return self.process.memory_info().rss / (1024 * 1024)


def count_log_errors():
    if not LOG_FILE.exists():
        return 0
    return sum(" - ERROR - " in line or " - CRITICAL - " in line for line in LOG_FILE.read_text(encoding="utf-8").splitlines())

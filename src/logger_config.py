import logging
import os
import sys

from config import BASE_DIR, LOG_FILE


class ConsoleFormatter(logging.Formatter):
    """Salida de consola ordenada: etapas como títulos y detalles indentados.

    El archivo pipeline.log mantiene el formato completo con fecha y nivel; esta
    clase solo afecta lo que se ve en la terminal.
    """

    STYLES = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[90m",
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
    }

    def __init__(self, use_color):
        super().__init__()
        self.use_color = use_color
        self.base = str(BASE_DIR) + os.sep

    def paint(self, text, *styles):
        if not self.use_color:
            return text
        prefix = "".join(self.STYLES[name] for name in styles)
        return f"{prefix}{text}{self.STYLES['reset']}"

    def format(self, record):
        # Rutas relativas para no llenar la consola con la ruta absoluta completa.
        message = record.getMessage().replace(self.base, "")

        if record.levelno >= logging.ERROR:
            return self.paint(f"✗ {message}", "bold", "red")
        if record.levelno >= logging.WARNING:
            return self.paint(f"⚠ {message}", "yellow")
        if message == "Inicio del pipeline":
            line = "═" * 50
            return self.paint(f"{line}\n  PIPELINE · RIESGO DE PRÉSTAMOS\n{line}", "bold", "blue")
        if message == "Fin del pipeline":
            return self.paint("\n✓ Pipeline finalizado correctamente", "bold", "green")
        if message.startswith("Etapa "):
            return "\n" + self.paint(f"▶ {message}", "bold", "blue")
        return self.paint("   ·", "dim") + f" {message}"


def setup_logger():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("loan_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Archivo: registro completo con fecha y nivel (evidencia y auditoría).
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    file_handler.setFormatter(file_formatter)

    # En Windows hay que habilitar la interpretación de códigos de color ANSI.
    if sys.platform == "win32":
        os.system("")

    # Consola: salida ordenada y legible. Sin color si no es terminal o si NO_COLOR.
    use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleFormatter(use_color))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

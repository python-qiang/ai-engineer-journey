"""
framework/logger.py - Unified logging for the project.

Auto-configures on first import. No manual setup call needed.

Usage in any module:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("something happened")

Configure in .env.dev:
    export LOG_LEVEL=INFO      # Options: DEBUG, INFO, WARNING, ERROR
    export LOG_OUTPUT=file     # Options: file, console, both

Logs file path: devenv_temp/logs/{entry_script_path}.log (append, rotating 5MB)
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "devenv_temp" / "logs"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_OUTPUT = os.environ.get("LOG_OUTPUT", "file").lower()  # file, console, both


def _get_entry_module_name() -> str:
    """Infer the log filename from the script that was directly executed.

    Returns relative path from src/ with dots, e.g. "week02_prompt.03a_sliding_window"
    """
    main_module = sys.modules.get("__main__")
    if main_module and hasattr(main_module, "__file__") and main_module.__file__:
        file_path = Path(main_module.__file__).resolve()
        src_dir = Path(__file__).resolve().parent.parent  # src/
        try:
            relative = file_path.relative_to(src_dir)
            return str(relative.with_suffix("")).replace(os.sep, ".")
        except ValueError:
            return file_path.stem
    return "app"


def _setup() -> None:
    """Configure root logger once. Called automatically on module load."""
    root_logger = logging.getLogger()

    if root_logger.hasHandlers():
        return

    level = getattr(logging, LOG_LEVEL, logging.INFO)
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if LOG_OUTPUT in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if LOG_OUTPUT in ("file", "both"):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            module_name = _get_entry_module_name()
            log_file = LOG_DIR / f"{module_name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=2
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            # Fall back to console if file fails
            fallback = logging.StreamHandler(sys.stderr)
            fallback.setLevel(level)
            fallback.setFormatter(formatter)
            root_logger.addHandler(fallback)


# Auto-setup on import
_setup()

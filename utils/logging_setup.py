"""Central logging configuration for the orchestrator.

Modules obtain their logger with ``logging.getLogger(__name__)`` and stay silent
about formatting; the entry point calls :func:`configure_logging` once so every
module shares a single coloured console format.
"""
import logging

import colorlog


def configure_logging(level: int = logging.INFO) -> None:
    """Install a single coloured console handler on the root logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

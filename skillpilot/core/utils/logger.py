"""Logging utilities"""

import structlog


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured logger instance"""
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


def configure_logging(debug: bool = False) -> None:
    """Configure structlog for the application"""
    log_level = "DEBUG" if debug else "INFO"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(structlog, log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

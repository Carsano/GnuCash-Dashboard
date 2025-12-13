"""Tests for the logging helpers."""

import logging
from unittest.mock import MagicMock

from src.infrastructure.logging import logger as logger_module


def test_logger_builder_creates_configured_logger(tmp_path, monkeypatch):
    """LoggerBuilder should build loggers in the project logs directory."""
    monkeypatch.setattr(
        logger_module,
        "get_project_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        logger_module.LoggerBuilder,
        "_today_stamp",
        staticmethod(lambda: "20240101"),
    )

    builder = logger_module.LoggerBuilder()
    custom_logger = (
        builder.name("custom")
        .subdir("etl")
        .prefix("etl_logs")
        .console(True)
        .level(logging.WARNING)
        .formatter(logger_module.LoggerBuilder._default_formatter)
        .file_handler(logger_module.LoggerBuilder._default_file_handler)
        .console_handler(logger_module.LoggerBuilder._default_console_handler)
        .build()
    )

    assert custom_logger.name == "custom"
    assert custom_logger.level == logging.WARNING
    file_handlers = [
        h
        for h in custom_logger.handlers
        if isinstance(h, logging.FileHandler)
    ]
    assert len(file_handlers) == 1
    expected_path = tmp_path / "logs" / "etl" / "20240101_etl_logs.log"
    assert file_handlers[0].baseFilename == str(expected_path)
    # Building again should reuse the same logger instance.
    assert builder.build() is custom_logger


def test_default_handlers_use_formatter(tmp_path):
    """Default handlers should apply the provided formatter."""
    fmt = logger_module.LoggerBuilder._default_formatter()
    file_handler = logger_module.LoggerBuilder._default_file_handler(
        tmp_path / "logs.log",
        fmt,
    )
    console_handler = logger_module.LoggerBuilder._default_console_handler(fmt)

    assert isinstance(file_handler, logging.FileHandler)
    assert file_handler.level == logging.INFO
    assert file_handler.formatter is fmt

    assert isinstance(console_handler, logging.StreamHandler)
    assert console_handler.level == logging.INFO
    assert console_handler.formatter is fmt


def test_logger_singleton_delegates_to_underlying_logger(monkeypatch):
    """Logger info/warning/error/etc. should call the wrapped logger."""
    fake_logger = MagicMock()
    monkeypatch.setattr(
        logger_module.LoggerBuilder,
        "build",
        lambda self: fake_logger,
    )
    logger_module.Logger._instance = None

    logger = logger_module.Logger("app")
    logger.info("hello")
    logger.warning("warn")
    logger.error("err")
    logger.debug("dbg")
    logger.critical("crit")

    fake_logger.info.assert_called_with("hello")
    fake_logger.warning.assert_called_with("warn")
    fake_logger.error.assert_called_with("err")
    fake_logger.debug.assert_called_with("dbg")
    fake_logger.critical.assert_called_with("crit")
    # Singleton check.
    assert logger_module.Logger("app") is logger


def test_app_and_usage_loggers_share_builder_singletons(monkeypatch):
    """get_app_logger and get_usage_logger should return singletons."""
    fake_logger = MagicMock()

    def _fake_build(self):
        return fake_logger

    monkeypatch.setattr(
        logger_module.LoggerBuilder,
        "build",
        _fake_build,
    )
    logger_module.AppLogger._instance = None
    logger_module.UsageLogger._instance = None

    app_logger_1 = logger_module.get_app_logger()
    app_logger_2 = logger_module.get_app_logger()
    usage_logger_1 = logger_module.get_usage_logger()
    usage_logger_2 = logger_module.get_usage_logger()

    assert app_logger_1 is app_logger_2
    assert usage_logger_1 is usage_logger_2
    assert isinstance(app_logger_1.logger, MagicMock)
    assert isinstance(usage_logger_1.logger, MagicMock)

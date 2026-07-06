from __future__ import annotations

import logging

from src.utils.log_utils import add_file_handler, get_logger


class TestGetLogger:
    def test_logger_returns_logger(self):
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

    def test_logger_reuses_handlers(self):
        logger = get_logger("test_reuse")
        count_before = len(logger.handlers)
        logger2 = get_logger("test_reuse")
        assert len(logger2.handlers) == count_before


class TestAddFileHandler:
    def test_file_handler_added(self, tmp_path):
        logger = get_logger("test_file_handler")
        log_path = tmp_path / "test.log"
        add_file_handler(logger, log_path)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_file_created(self, tmp_path):
        logger = get_logger("test_file_created")
        log_path = tmp_path / "sub" / "test.log"
        add_file_handler(logger, log_path)
        assert log_path.parent.exists()

import logging


def pytest_configure() -> None:
    logging.disable(logging.CRITICAL)

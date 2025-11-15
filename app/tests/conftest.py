from collections.abc import Generator  # noqa

import pytest

from app.core.log_adapter import setup_logging


@pytest.fixture(autouse=True)
def init_logger(request: pytest.FixtureRequest) -> None:
    _level = request.config.getini("log_cli_level")
    setup_logging(json_logs=False, log_level=_level)

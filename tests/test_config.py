from __future__ import annotations

from src.config import Config, config


class TestConfig:
    def test_load_config(self):
        cfg = Config.from_yaml()
        assert cfg is not None

    def test_missing_config_returns_default(self, tmp_path):
        missing = tmp_path / "nonexistent" / "config.yml"
        cfg = Config.from_yaml(missing)
        assert cfg.logging.level == "INFO"

    def test_config_has_logging(self):
        assert hasattr(config, "logging")

    def test_config_has_data(self):
        assert hasattr(config, "data")

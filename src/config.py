from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class DataConfig:
    raw_path: str = "data/raw"
    processed_path: str = "data/processed"
    source: str = "synthetic"
    allowed_root: str | None = None
    column_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "case_id": "case:concept:name",
            "activity": "concept:name",
            "timestamp": "time:timestamp",
        }
    )


@dataclass
class DiscoveryConfig:
    algorithm: str = "inductive"
    variant: str = "IMd"
    noise_threshold: float = 0.2


@dataclass
class ConformanceConfig:
    method: str = "token_based"
    model_path: str = "data/normative/o2c_sop.pnml"


@dataclass
class AnalysisConfig:
    top_variants: int = 10
    bottleneck_percentile: int = 90


@dataclass
class VisualizationConfig:
    dashboard_port: int = 8501
    petri_format: str = "svg"
    max_dfg_nodes: int = 50


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "logs/pipeline.log"


@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    conformance: ConformanceConfig = field(default_factory=ConformanceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> Config:
        path = path or DEFAULT_CONFIG_PATH
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        cfg = cls()
        if "data" in data:
            cfg.data = DataConfig(**data["data"])
        if "discovery" in data:
            cfg.discovery = DiscoveryConfig(**data["discovery"])
        if "conformance" in data:
            cfg.conformance = ConformanceConfig(**data["conformance"])
        if "analysis" in data:
            cfg.analysis = AnalysisConfig(**data["analysis"])
        if "visualization" in data:
            cfg.visualization = VisualizationConfig(**data["visualization"])
        if "logging" in data:
            cfg.logging = LoggingConfig(**data["logging"])
        return cfg


config = Config.from_yaml()

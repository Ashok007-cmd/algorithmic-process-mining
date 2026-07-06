from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import pm4py

from src.config import Config
from src.config import config as default_config
from src.conformance.comparison import compare_methods, compare_to_normative
from src.data.generators.synthetic import generate_o2c_log, generate_p2p_log
from src.data.pipeline import run_pipeline
from src.discovery.inductive import discover_inductive
from src.utils.log_utils import get_logger, setup_logging

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Algorithmic Process Mining")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate synthetic event log")
    gen.add_argument("--process", choices=["o2c", "p2p"], required=True)
    gen.add_argument("--cases", type=int, default=100)
    gen.add_argument("--noise", type=float, default=0.0)
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--output", type=Path, required=True)

    runp = sub.add_parser("run", help="Load, transform, and validate an event log")
    runp.add_argument("--input", type=Path, required=True)
    runp.add_argument("--output", type=Path, required=True)
    runp.add_argument("--anonymize", action="store_true", help="Hash case IDs before writing output")
    runp.add_argument("--salt", default=None, help="Salt for anonymization (default: $ANONYMIZER_SALT)")
    runp.add_argument("--config", type=Path, default=None, help="Path to a config.yaml to use instead of the default")

    disc = sub.add_parser("discover", help="Discover a Petri net from an event log")
    disc.add_argument("--input", type=Path, required=True)
    disc.add_argument("--output", type=Path, required=True, help="Output PNML path")
    disc.add_argument("--variant", choices=["im", "imf", "imd"], default=None)
    disc.add_argument("--noise-threshold", type=float, default=None)
    disc.add_argument("--config", type=Path, default=None)

    conf = sub.add_parser("conformance", help="Check conformance of an event log against a model")
    conf.add_argument("--input", type=Path, required=True)
    conf.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Normative PNML model to compare against (default: config.conformance.model_path). "
        "If omitted and no default exists, a model is discovered from the input log instead.",
    )
    conf.add_argument("--output", type=Path, required=True, help="Output JSON path")
    conf.add_argument("--config", type=Path, default=None)

    return parser


def _resolve_config(config_path: Path | None) -> Config:
    return Config.from_yaml(config_path) if config_path else default_config


def _write_event_log(df: pd.DataFrame, output_path: Path) -> Path:
    if output_path.suffix == ".parquet":
        df.to_parquet(output_path, index=False)
        return output_path
    actual_path = output_path if output_path.suffix == ".csv" else output_path.with_suffix(".csv")
    df.to_csv(actual_path, index=False)
    return actual_path


def cmd_generate(args: argparse.Namespace) -> None:
    try:
        fn = generate_o2c_log if args.process == "o2c" else generate_p2p_log
        df = fn(n_cases=args.cases, noise_level=args.noise, seed=args.seed)
        actual_path = _write_event_log(df, Path(args.output))
        logger.info("Generated %s log -> %s", args.process, actual_path)
    except Exception:
        logger.exception("Failed to generate log")
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> None:
    try:
        cfg = _resolve_config(args.config)
        salt = args.salt if args.salt is not None else ""
        df = run_pipeline(
            Path(args.input),
            column_mapping=cfg.data.column_mapping,
            anonymize=args.anonymize,
            salt=salt,
        )
        actual_path = _write_event_log(df, Path(args.output))
        logger.info("Pipeline output -> %s", actual_path)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)


def cmd_discover(args: argparse.Namespace) -> None:
    try:
        cfg = _resolve_config(args.config)
        df = run_pipeline(Path(args.input), column_mapping=cfg.data.column_mapping)
        variant = args.variant or cfg.discovery.variant
        noise_threshold = args.noise_threshold if args.noise_threshold is not None else cfg.discovery.noise_threshold
        net, im, fm = discover_inductive(df, noise_threshold=noise_threshold, variant=variant)
        pm4py.write_pnml(net, im, fm, str(args.output))
        logger.info(
            "Discovered model (%s, %d places, %d transitions) -> %s",
            variant,
            len(net.places),
            len(net.transitions),
            args.output,
        )
    except Exception:
        logger.exception("Discovery failed")
        sys.exit(1)


def cmd_conformance(args: argparse.Namespace) -> None:
    try:
        cfg = _resolve_config(args.config)
        df = run_pipeline(Path(args.input), column_mapping=cfg.data.column_mapping)

        model_path = args.model or Path(cfg.conformance.model_path)
        if model_path.exists():
            result = compare_to_normative(df, model_path)
        else:
            logger.warning("Normative model %s not found; discovering a model from the input log instead", model_path)
            net, im, fm = discover_inductive(df, noise_threshold=cfg.discovery.noise_threshold, variant=cfg.discovery.variant)
            result = compare_methods(df, net, im, fm)
            result["normative_model"] = None

        args.output.write_text(json.dumps(result, indent=2))
        logger.info("Conformance results (delta_fitness=%.4f) -> %s", result["delta_fitness"], args.output)
    except Exception:
        logger.exception("Conformance check failed")
        sys.exit(1)


def main() -> None:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()
    commands = {
        "generate": cmd_generate,
        "run": cmd_run,
        "discover": cmd_discover,
        "conformance": cmd_conformance,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

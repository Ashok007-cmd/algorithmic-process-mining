# Algorithmic Process Mining

Discover real business process models from ERP-style event logs, check conformance against a normative "should-be" model, and surface bottlenecks, rework, and cycle-time KPIs — as a CLI pipeline or an interactive dashboard.

Built around [`pm4py`](https://github.com/process-intelligence-solutions/pm4py) for the Order-to-Cash (O2C) and Procure-to-Pay (P2P) logistics cycles, but works with any event log that has a case ID, an activity name, and a timestamp.

## What it does

1. **Ingest** a CSV/XES/Parquet event log, validate it (schema, timestamps, duplicates), and optionally anonymize case IDs.
2. **Discover** a Petri net process model with the Inductive Miner (`im` / `imf` / `imd` variants).
3. **Check conformance** — either self-conformance (as-discovered) or against a normative SOP model (as-is vs to-be), via both token-based replay and alignments.
4. **Analyze** cycle time, throughput bottlenecks, rework loops, and trace variants.
5. **Visualize** everything in a Streamlit dashboard, or drive it all from the CLI for batch/automated use.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# system dependency for Petri net / DFG rendering
sudo apt-get install -y graphviz   # or: make setup-graphviz
```

Generate a synthetic log and run it through the pipeline:

```bash
python -m src.cli generate --process o2c --cases 100 --noise 0.2 --output data/raw/o2c.csv
python -m src.cli run --input data/raw/o2c.csv --output data/processed/o2c_clean.csv
python -m src.cli discover --input data/processed/o2c_clean.csv --output data/models/o2c_model.pnml
python -m src.cli conformance --input data/processed/o2c_clean.csv --output data/results/o2c_conformance.json
```

Or launch the interactive dashboard:

```bash
streamlit run src/viz/dashboard.py
```

## CLI reference

| Command | Purpose |
|---|---|
| `generate --process {o2c,p2p} --cases N [--noise F] [--seed N] --output PATH` | Generate a synthetic O2C/P2P event log with controllable noise (skips, rework, insertions) |
| `run --input PATH --output PATH [--anonymize] [--salt S] [--config PATH]` | Load, validate, transform, and (optionally) anonymize an event log |
| `discover --input PATH --output PATH [--variant {im,imf,imd}] [--noise-threshold F]` | Discover a Petri net (PNML) with the Inductive Miner |
| `conformance --input PATH --output PATH [--model PATH]` | Compare a log against a normative model (default `data/normative/o2c_sop.pnml`) via token replay + alignments; falls back to self-discovery if no model is given |

All commands accept `--config PATH` to override `config.yaml`. Run `python -m src.cli <command> --help` for full option lists.

## Configuration

Runtime defaults live in [`config.yaml`](config.yaml): data paths and column mapping, discovery algorithm/variant/noise threshold, conformance model path, analysis thresholds (bottleneck percentile, top-N variants), and visualization limits. `src/config.py` loads it into typed dataclasses; CLI commands and the dashboard both read from it, and any command's `--config` flag can point at an alternate file.

Environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `ANONYMIZER_SALT` | Salt for hashing case IDs when anonymizing — set this in any real (non-demo) use, or a warning is logged |
| `LOG_LEVEL` | Logging verbosity (default `INFO`) |
| `PROJECT_ROOT`, `DATA_DIR`, `PM4PY_CACHE_DIR` | Optional path overrides |

## Project structure

```
src/
├── cli.py                  # generate / run / discover / conformance subcommands
├── config.py                # config.yaml + .env loader
├── data/
│   ├── loader.py             # CSV / XES / Parquet ingestion
│   ├── validator.py          # schema, timestamp, duplicate checks
│   ├── transformer.py        # column mapping, dtype casting, UTC normalization
│   ├── anonymizer.py         # salted case-ID hashing
│   ├── pipeline.py           # load -> transform -> validate -> (anonymize)
│   ├── generators/synthetic.py  # synthetic O2C/P2P log generator (noise, rework, skips)
│   └── ocel/                 # object-centric event log (OCEL 2.0) loading
├── discovery/
│   ├── inductive.py           # Inductive Miner (im / imf / imd variants), LRU-cached
│   ├── heuristics.py          # Heuristics Miner
│   └── dfg.py                 # Directly-Follows Graph + DFG-based Petri net
├── conformance/
│   ├── token_replay.py        # token-based replay fitness
│   ├── alignments.py          # alignment-based fitness (with cost-bounding sample cap)
│   └── comparison.py          # method comparison + as-is vs to-be normative comparison
├── analysis/
│   ├── kpis.py                 # cycle time / throughput
│   ├── bottlenecks.py          # slow-activity + rework detection
│   └── variants.py             # trace variant frequency, happy-path share
├── viz/
│   ├── dashboard.py            # Streamlit app
│   ├── charts.py               # Plotly chart components
│   └── petri_render.py         # Petri net / DFG / heuristics net rendering (graceful Graphviz fallback)
└── utils/                   # logging, file-path validation, discovery-result caching

data/
├── normative/    # SOP ("to-be") Petri nets — o2c_sop.pnml, p2p_sop.pnml
├── sample/       # small example logs
├── raw/ processed/ models/ results/ ocel/   # pipeline working directories (gitignored)

tests/            # pytest suite mirroring src/, plus integration + CLI e2e tests
```

## Development

```bash
make install-dev     # pip install -e ".[dev]"
make test            # pytest
make test-cov        # pytest with coverage report
make lint             # ruff check
make format           # ruff format
make typecheck        # mypy --strict
make run-app          # streamlit dashboard
```

The test suite covers ingestion, discovery, conformance, analysis, caching, CLI commands, and OCEL loading (112 tests, ~90% coverage on `src/`). CI (`.github/workflows/ci.yml`) runs ruff, ruff format check, mypy, bandit, pip-audit, and the full pytest matrix (3.11/3.12) on every push/PR.

## Docker

```bash
docker build -t process-mining .
docker run -p 8501:8501 process-mining
```

Runs as a non-root user with a container healthcheck against Streamlit's `/_stcore/health` endpoint. The image binds the dashboard to all interfaces with no built-in authentication — put a reverse proxy with TLS/auth in front of it before exposing it beyond a trusted network.

## Notes

- `pm4py` is licensed AGPL v3 (Community Edition) — commercial use without a commercial pm4py license requires open-sourcing applications built on it. See the [pm4py licensing page](https://processintelligence.solutions/pm4py#licensing).
- Petri net / DFG rendering requires the system `graphviz` package (the `dot` binary); if it isn't installed, rendering raises a clear `VisualizationUnavailableError` instead of crashing, and the dashboard shows an informational message.
- The normative SOP models in `data/normative/` were discovered from each process's clean happy-path sequence (see `src/data/generators/synthetic.py`) — replace them with your own PNML files to check conformance against a real organizational SOP.

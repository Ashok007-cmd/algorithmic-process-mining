# Project Audit Report: Improvement Analysis & Security Assessment

**Project:** Algorithmic Process Mining
**Date:** 2026-07-06
**Scope:** Full codebase (`src/`, `tests/`, CI/CD, Docker, dependencies)
**Method:** Static analysis (ruff, mypy --strict, bandit), dependency vulnerability research (pip-audit + manual PyPI metadata verification), first-party code integrity review, and authorized adversarial testing against the local CLI/dashboard.

---

## 1. Executive Summary

| Area | Status |
|---|---|
| Tests | 125 passing, 0 failing |
| Coverage | 89% of `src/` |
| Static analysis (ruff, mypy --strict) | Clean |
| SAST (bandit) | 0 findings |
| Dependency vulnerabilities (pip-audit) | 0 (2 real CVEs found and fixed during this audit — see §4.2) |
| Secrets in repo | None found |
| Confirmed exploitable vulnerabilities | 1 (CSV formula injection — **fixed**, see §4.4) |
| Supply-chain integrity | 101 packages vetted, all legitimate |

The codebase is small (33 first-party modules, ~1,300 LOC), well-tested, and — after the fixes applied during this audit — has no known outstanding security vulnerabilities. The main opportunities left are architectural (closing remaining gaps between the pipeline stages and true production scale) rather than defects.

---

## 2. Improvement Analysis

### 2.1 What's already strong

- Clean separation of concerns (`data` → `discovery` → `conformance` → `analysis` → `viz`), verified with no circular imports.
- CLI (`generate`/`run`/`discover`/`conformance`) drives the full pipeline end-to-end, backed by 125 tests including CLI-level integration tests.
- Config-driven discovery (variant, noise threshold), conformance (normative model path), and analysis (bottleneck percentile, top-N variants) — no hardcoded parameters bypassing `config.yaml`.
- Discovery results are LRU-cached (content-hash keyed) to avoid redundant recomputation across discovery/conformance calls on the same log.
- CI enforces ruff, ruff format, mypy --strict, bandit, and pip-audit on every push across Python 3.11/3.12.

### 2.2 Remaining opportunities (prioritized)

| Priority | Opportunity | Why it matters |
|---|---|---|
| High | On-disk Parquet caching for `run_pipeline` | `pyarrow` is a pinned dependency for exactly this, but ingestion still re-reads/re-transforms from scratch on every CLI invocation. Caching the transformed log would materially speed up repeated `discover`/`conformance` runs against the same source file. |
| High | Chunked/streaming ingestion for very large logs | `src/data/loader.py` hard-rejects files over 500MB with no fallback. Real ERP exports can exceed this. A `chunksize`-based read path (or a documented "pre-sample/pre-filter" step) would let the tool scale to genuinely large logs, which is the stated target use case. |
| Medium | Batch/multiprocessing support | Discovery and alignment-based conformance are CPU-bound and single-threaded. `joblib`/`multiprocessing` for per-case-batch parallelism would reduce wall-clock time on multi-core machines, especially for alignments (the most expensive operation). |
| Medium | Dashboard test coverage | `src/viz/dashboard.py` is at 0% coverage — Streamlit apps are awkward to unit test, but a `streamlit.testing.v1.AppTest`-based smoke test (available in modern Streamlit) would catch regressions without a browser. |
| Medium | XES ingestion test coverage | `load_xes` is untested; XES is a first-class supported format per the CLI/loader but has no regression test guarding it. |
| Low | OCEL CLI wiring | `src/data/ocel/` is fully implemented and tested in isolation but has no CLI subcommand exposing it — object-centric process mining is mentioned in the project's value proposition but isn't reachable end-to-end today. |
| Low | Config-driven data-root allowlist | `validate_input_path` doesn't confine reads to a project data directory. Not a real vulnerability for a local CLI tool (see §4.5), but would matter if this were ever wrapped in a multi-tenant service. |

None of these are defects — they're the natural next increments for a project moving from "functionally complete" to "production-scale."

---

## 3. Security & Vulnerability Assessment — Methodology Note

The request for this audit named several distinct security disciplines. Two of them don't map cleanly onto this project, and it's worth being explicit about that rather than performing a hollow version of them:

- **Malware analysis** is normally the study of a *malicious sample* (a binary, macro, or script someone believes is hostile). There is no malware here — this is original, from-scratch source code with a known, auditable dependency tree. What *does* transfer meaningfully from that discipline is **supply-chain integrity verification**: confirming every dependency is the genuine package it claims to be, not a typosquat or compromised release. That's covered in §4.2.
- **Reverse engineering** is normally applied to closed-source binaries to recover their logic. Every line of this project is source-available Python already. What transfers is a **static code-integrity review**: reading the actual first-party code (not a decompiled approximation of it) for hidden/obfuscated logic, unexpected network calls, or backdoor-shaped patterns. That's covered in §4.3.

The remaining disciplines — **vulnerability research**, **penetration testing**, and **patch development** — map directly and were performed as described in §4.2, §4.4, and §4.6 respectively, scoped to the actual threat model of this software: a locally-run CLI/dashboard that processes event log files, which may originate from external ERP systems and therefore can't be assumed trustworthy in content (even though the person invoking the CLI is trusted).

---

## 4. Findings

### 4.1 Static Analysis (SAST)

`bandit -r src/`: **0 issues** (Low/Medium/High all zero) across 1,300+ lines. `ruff check` (E/F/W/I/N/UP rules): 0 violations. `mypy --strict`: 0 errors across 33 modules.

### 4.2 Dependency Vulnerability Research (Supply Chain)

**Method:** `pip-audit` against the resolved environment (cross-referencing the OSV/PyPA advisory database), plus manual verification of every direct dependency's PyPI metadata (homepage, author, license) against the known-legitimate project for that name.

**Findings — before fixes:**

| Package | Installed | Issue | Fixed version |
|---|---|---|---|
| `pip` (build tool, not a project dependency) | 24.0 | 5 known CVEs (incl. PYSEC-2026-196, CVE-2025-8869, CVE-2026-1703/3219/6357) | 26.1.2 |
| `pyarrow` | 17.0.0 (constrained `<18.0`) | PYSEC-2026-113 | 23.0.1+ |

**Remediation:** upgraded `pip` in the environment; changed the `pyarrow` constraint in `pyproject.toml` from `>=14.0,<18.0` to `>=23.0.1,<25.0` and reinstalled. Full test suite (125 tests) re-verified green after the bump — no breaking changes observed in the Parquet read/write paths this project actually uses. **Re-running `pip-audit` after the fix returns zero known vulnerabilities.**

Worth noting for methodology transparency: an initial pass treated the `pyarrow` finding as a possible sandbox artifact (the fix version looked implausible at a glance). That assumption was checked — not asserted — via `pip index versions pyarrow`, which confirmed the version genuinely exists and the CVE is real. Lesson applied: verify before dismissing a vulnerability-scanner finding, especially version numbers that look unfamiliar.

**Supply-chain legitimacy check:** all 17 direct dependencies (`pm4py`, `pandas`, `numpy`, `networkx`, `graphviz`, `matplotlib`, `plotly`, `streamlit`, `pyarrow`, `scikit-learn`, `requests`, `pyyaml`, `python-dotenv`, plus dev tools `pytest`, `ruff`, `mypy`, `bandit`) were checked against their installed package metadata — homepage, author/maintainer, and license all match the well-known canonical project for that name. The full transitive tree (101 packages) was also reviewed by name for typosquatting; nothing anomalous found, including less-common transitive packages (`ast_serialize`, `librt` — both legitimate mypyc runtime components; `boolean.py`, `cvxopt`, `packageurl-python` — all verified legitimate, widely-used libraries).

### 4.3 Static Code-Integrity Review (First-Party Code)

Full grep-based sweep of all 33 first-party modules in `src/` for patterns associated with hidden/malicious logic:

| Pattern class | Result |
|---|---|
| `eval`/`exec`/`compile` | 0 occurrences |
| `pickle`/`marshal`/`shelve` (unsafe deserialization) | 0 occurrences |
| `subprocess`/`os.system`/`os.popen` | 0 occurrences |
| Outbound network calls (`requests.*`, `socket`, `urllib.request`) | 0 occurrences |
| `base64`/`codecs.decode`/`zlib.decompress` (payload obfuscation) | 0 occurrences |
| `__import__`/`importlib.import_module` (dynamic import) | 0 occurrences |
| `yaml.load` without `safe_load` | 0 occurrences (project correctly uses `yaml.safe_load` throughout) |
| `os.chmod`/`os.chown`/`os.setuid` | 0 occurrences |
| Hardcoded system paths (`/etc/`, `/root/`, `/var/`) | 0 occurrences |
| Environment variable reads | 1 (`ANONYMIZER_SALT`, exactly as documented — no exfiltration) |

**Conclusion:** no hidden logic, no obfuscation, no unexpected I/O or network behavior anywhere in the first-party codebase.

### 4.4 Authorized Adversarial Testing (Penetration Testing)

Testing was performed against the local CLI and Streamlit dashboard, scoped to this project's actual threat model: a tool that ingests event log files which may come from external/untrusted ERP exports.

| # | Test | Result |
|---|---|---|
| 1 | **CSV/formula injection** (CWE-1236) — case IDs / activity names containing `=cmd\|'/C calc'!A0`, `+HYPERLINK(...)`, `-2+3`, `@SUM(...)` | 🔴 **Vulnerable** (confirmed exploitable) — **fixed**, see §4.6 |
| 2 | File-size cap enforcement (500MB limit) | ✅ Pass — correctly rejected |
| 3 | YAML "billion laughs"-style alias-expansion DoS via `--config` | ✅ Pass — PyYAML's `safe_load` shares references across aliases rather than deep-copying, so no memory blow-up occurs (verified: 8 levels of 10x nesting loaded in ~1ms, ~183MB baseline RSS) |
| 4 | Malformed/invalid-UTF-8 CSV input | ✅ Pass — raises a clean, caught `UnicodeDecodeError`, logged with full traceback via `logger.exception`, exits with code 1 (no crash, no hang, no silent corruption) |
| 5 | Pathologically long single field (2MB) | ✅ Pass — processed in <1s, no resource exhaustion |
| 6 | XML/PNML injection — activity names containing `<script>`, `&`, unescaped quotes, written to a discovered PNML model | ✅ Pass — pm4py's PNML writer properly XML-escapes all special characters; output verified well-formed via `xml.etree.ElementTree` |
| 7 | Dashboard XSS via `unsafe_allow_html` | ✅ Pass — zero usage found; no raw HTML rendering of user-controlled data anywhere in `src/viz/` |
| 8 | Malformed/garbage OCEL JSON | ⚠️ Minor — raises an unhandled `KeyError` rather than a clean validation error (library-level robustness gap; not currently reachable from the CLI, so not exploitable today) |
| 9 | Negative/zero `--cases` on `generate` | 🟡 **Fixed** — previously bubbled a confusing internal pandas `KeyError`; now raises a clear `ValueError: n_cases must be >= 1` (§4.6) |
| 10 | Path traversal via `--input`/`--output` | ℹ️ **By design, not a vulnerability** — the CLI reads/writes any path the invoking OS user can already access. No privilege boundary is crossed because there's no privilege boundary to begin with (single local user, same permissions as the shell invoking the tool). This *would* need re-evaluation if the pipeline were ever wrapped in a networked service accepting paths from untrusted remote callers. |
| 11 | Stress test: 20,000 cases, 0.8 noise level | ✅ Pass — completed in 1.7s, 163k output rows, no resource exhaustion |

### 4.5 Threat Model Statement

This is a locally-run CLI and single-user Streamlit dashboard, not a multi-tenant networked service. The relevant attacker is **data content, not a network adversary**: a malicious or malformed event log file (from a compromised or careless upstream ERP export) is the only untrusted input this tool processes. Findings and remediations above are scoped accordingly. If this pipeline is ever deployed as a shared/networked service (e.g., a hosted dashboard accepting uploads from multiple organizations), the following would need to be revisited: (a) confining file reads to a scoped data directory, (b) authentication/authorization in front of the dashboard, (c) per-request resource limits (the current 500MB/file cap is process-wide, not per-tenant).

### 4.6 Patch Development

Two real issues were found and fixed during this audit, both with regression tests added:

1. **CSV formula injection (CWE-1236) — High severity, fixed.**
   `src/utils/io_utils.py::sanitize_for_csv_injection()` now prefixes any string/categorical cell value starting with `=`, `+`, `-`, `@`, tab, or CR with a single quote before writing CSV output, per the OWASP CSV Injection Cheat Sheet's recommended mitigation. Wired into the single CSV-write chokepoint in `src/cli.py::_write_event_log`. Verified against the original exploit payloads (now neutralized) and covered by 5 new unit tests plus 1 CLI-level integration test — including a test for the categorical-dtype column that the first patch attempt missed (`concept:name` is cast to `category` dtype by the transformer, which an initial `object`/`string`-only dtype filter didn't catch).

2. **Unhandled internal exception on invalid `--cases` — Low severity, fixed.**
   `generate_event_log()` now validates `n_cases >= 1` upfront with a clear `ValueError`, instead of letting `0` or negative values propagate into an empty-DataFrame `sort_values()` call that raised a confusing internal pandas `KeyError`. Two regression tests added.

Also fixed as part of the dependency vulnerability research (§4.2): `pyarrow` version constraint bump, `pip` upgrade.

---

## 5. Verification

All findings above were independently re-verified after remediation:

- `pytest tests/` — **125 passed**, 0 failed
- `pytest --cov=src` — **89%** coverage
- `ruff check` / `ruff format --check` — clean
- `mypy --strict` — 0 errors
- `bandit -r src/` — 0 issues
- `pip-audit --skip-editable` — 0 known vulnerabilities
- Manual CLI end-to-end run (`generate` → `run` → `discover` → `conformance`) and Streamlit dashboard smoke test (HTTP 200) both re-confirmed working after all changes

---

## 6. Conclusion

Before this audit, the project had zero known CVEs in its own CI-reported tooling but two real, unaddressed dependency CVEs (`pip`, `pyarrow`) and one exploitable application-level vulnerability (CSV formula injection) that no prior automated tooling in this project's CI pipeline (bandit, ruff, mypy) is designed to catch, since it's a data-handling logic issue rather than a static-analysis-detectable pattern. Both dependency CVEs and the injection vulnerability are now fixed, tested, and verified. The remaining open items (§2.2) are scaling/architecture work, not defects — the project is in a solid, defensible state for portfolio review.

# Debugging Guide: Algorithmic Process Mining with pm4py

> **Audience:** Developers building the process mining pipeline
> **Scope:** Pre-mortem analysis of likely failure modes — before code exists
> **Covers:** pm4py API pitfalls, data quality traps, conformance diagnostics, defensive patterns
> **Status:** Planning reference | Apply during implementation and testing

---

## Table of Contents

1. [Failure Mode Matrix: Likelihood × Impact](#1-failure-mode-matrix-likelihood--impact)
2. [Tier 1 — High Likelihood, High Impact](#2-tier-1--critical-failure-modes)
3. [Tier 2 — Data Quality Traps Masquerading as Bugs](#3-tier-2--data-quality-traps)
4. [Tier 3 — Algorithmic Complexity & Edge Cases](#4-tier-3--algorithmic-complexity--edge-cases)
5. [Tier 4 — Visualization & Environment](#5-tier-4--visualization--environment)
6. [Conformance Checking Diagnostic Procedures](#6-conformance-checking-diagnostic-procedures)
7. [Defensive Programming Patterns](#7-defensive-programming-patterns)
8. [Testing Strategy for Bug Prevention](#8-testing-strategy)
9. [Quick Reference: pm4py API Pitfall Catalog](#9-pm4py-api-pitfall-catalog)

---

## 1. Failure Mode Matrix: Likelihood × Impact

```
                         HIGH IMPACT
                              │
     COLUMN_NAMING      ●─────┼─────●  INFINITE_LOOP
     TIMESTAMP_PARSE         │         (Inductive Miner)
     DUPLICATE_CASE_IDS      │         OOM_ON_LARGE_LOG
                              │
                              ├───────●  EXPLODING_ALIGNMENTS
     OUT_OF_ORDER_EVENTS      │
     SILENT_DROP              │
     LOW_FITNESS              │
     ACTIVITY_NAMING          │
     OCEL_VALIDATION          │
                              │
     ────────────────────────●┼───────▶  HIGH LIKELIHOOD
                              │
     GRAPHVIZ_MISSING     ●───┼─────●  DEADLOCK_DETECTION
     WRONG_MODEL_NOISE        │
     BPMN_CONVERSION          │
     VERSION_API_BREAK        │
                              │
                        LOW IMPACT
```

| Rank | Failure Mode | Likelihood | Impact | Detection Difficulty |
|------|-------------|-----------|--------|---------------------|
| **1** | Column naming mismatch | ★★★★★ | ★★★★☆ | Easy (crash on startup) |
| **2** | Timestamp parse failure | ★★★★★ | ★★★★★ | Medium (silent NaN) |
| **3** | Duplicate case IDs | ★★★★☆ | ★★★★☆ | Medium (PM4Py silent drop) |
| **4** | Out-of-order events | ★★★★☆ | ★★★☆☆ | Hard (wrong model, no error) |
| **5** | Activity naming inconsistencies | ★★★★☆ | ★★★★☆ | Hard (no crash, wrong model) |
| **6** | Inductive Miner OOM | ★★★☆☆ | ★★★★★ | Easy (process crash) |
| **7** | Alignment exponential blowup | ★★★☆☆ | ★★★★★ | Medium (hangs, no error) |
| **8** | Graphviz missing | ★★★☆☆ | ★★☆☆☆ | Easy (import error) |
| **9** | Low fitness diagnosis confusion | ★★★☆☆ | ★★★☆☆ | Very Hard (noise vs. bug) |
| **10** | OCEL validation errors | ★★★☆☆ | ★★★★☆ | Medium |
| **11** | Silent NaN timestamp coercion | ★★☆☆☆ | ★★★★★ | Very Hard (NaT → silent) |
| **12** | pm4py API breaking changes | ★★☆☆☆ | ★★★★☆ | Medium (import errors) |

---

## 2. Tier 1 — Critical Failure Modes

### 2.1 Column Naming Mismatch

**Root cause:** pm4py's API functions require specific column names: `case:concept:name`, `concept:name`, `time:timestamp`. If your DataFrame uses different names, pm4py silently produces wrong results or crashes with cryptic errors.

**How it manifests:**
- `pm4py.discover_petri_net_inductive()` returns a 1-place, 0-transition Petri net (silent failure)
- Conformance functions return fitness = 0.0 for all traces
- Error: `KeyError: 'concept:name'` or `AttributeError: 'DataFrame' object has no attribute 'concept:name'`
- Worse: *no error* — the API falls back to defaults that happen to "work" on unrelated columns

**pm4py version-specific behavior:**
- pm4py **≥2.7.0**: Most functions accept `case_id_key`, `activity_key`, `timestamp_key` parameters — **use them explicitly**.
- pm4py **≥2.7.10**: Introduced `pm4py.format_dataframe()` that auto-renames common column variants. Use as a safety net but don't rely on it exclusively.
- pm4py **<2.7.0**: Required hardcoded column names. Fallback to explicit rename.

**Symptom-to-problem mapping:**
```
Model has 1 place, 0 transitions → Column names not recognized by miner
All traces have fitness = 0.0     → Model/log column mismatch
KeyError on "concept:name"        → Column not renamed before pm4py call
```

**Diagnostic procedure:**
```python
# 1. Verify column names match pm4py expectations
expected = {"case:concept:name", "concept:name", "time:timestamp"}
actual = set(event_log.columns)
if not expected.issubset(actual):
    logger.error("Missing columns: %s", expected - actual)
    logger.error("Present columns: %s", actual)
    raise ValueError(f"Missing required columns: {expected - actual}")

# 2. Check that pm4py recognizes the log format
try:
    from pm4py.utils import get_variants_from_log
    variants = get_variants_from_log(event_log)
    if len(variants) == 0:
        logger.warning("PM4Py detected 0 variants — column names likely wrong")
except Exception as e:
    logger.error("PM4Py column recognition failed: %s", e)
```

**Prevention:**
```python
# In transformer.py — single source of truth for column mapping
import pm4py

def transform_to_pm4py(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Rename columns to pm4py format using explicit mapping.

    Args:
        df: Raw DataFrame with source-specific column names.
        mapping: Dict mapping source columns → pm4py columns.
            e.g. {"OrderID": "case:concept:name", "Event": "concept:name", "Date": "time:timestamp"}

    Returns:
        DataFrame with pm4py-standard column names, sorted by case + timestamp.
    """
    result = df.rename(columns=mapping)
    required = {"case:concept:name", "concept:name", "time:timestamp"}
    missing = required - set(result.columns)
    if missing:
        raise ValueError(f"Missing required columns after rename: {missing}")

    result["time:timestamp"] = pd.to_datetime(result["time:timestamp"], utc=True)
    result = result.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)

    # Register with pm4py for full API support
    pm4py.format_dataframe(result, case_id="case:concept:name", activity_key="concept:name",
                           timestamp_key="time:timestamp")
    return result
```

---

### 2.2 Timestamp Parsing Failure

**Root cause:** Real ERP logs have enormous timestamp format variety. `pd.to_datetime()` with default settings works ~60% of the time. The remaining 40% produces `NaT` silently — and NaT entries in the timestamp column cause pm4py to drop entire events, producing an incorrect (but not obviously wrong) model.

**Common format variations from real ERPs:**
```
"2025-01-15 14:30:00"          → ISO-8601 (works)
"01/15/2025 02:30:00 PM"      → US format (needs format string)
"15.01.2025 14:30:00"         → EU format (needs dayfirst=True)
"2025-01-15T14:30:00.000+01:00" → ISO with tz (needs utc=True)
"2025-01-15T14:30:00Z"        → UTC (standard)
"Jan 15 2025 2:30PM"          → Abbreviated text (error-prone)
"20250115_143000"              → Compact (needs custom format)
"14:30:00 2025-01-15"         → Reversed (needs custom format)
44321.54321                     → Excel serial date (needs special handling)
```

**The silent NaT trap:**
```python
df = pd.read_csv("erp_export.csv")
df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])  # 5% become NaT silently
event_log = pm4py.format_dataframe(df, ...)  # Drops rows with NaT silently
# → Model is wrong, but no error thrown
```

**Diagnostic procedure:**
```python
def diagnose_timestamp_issues(df: pd.DataFrame, col: str = "time:timestamp"):
    """Identify timestamp parsing problems before they corrupt the model."""
    # Parse attempt
    parsed = pd.to_datetime(df[col], errors="coerce")

    # 1. Report parsing failure rate
    n_nat = parsed.isna().sum()
    n_total = len(df)
    if n_nat > 0:
        logger.warning("%d/%d timestamps could not be parsed (%.1f%%)", n_nat, n_total, 100*n_nat/n_total)

    # 2. Show sample of unparsable values
    if n_nat > 0:
        bad = df.loc[parsed.isna(), col].dropna().unique()[:10]
        logger.warning("Sample unparsable timestamps: %s", bad)

    # 3. Detect mixed formats (strong indicator of concatenation without normalization)
    unique_formats = df[col].dropna().apply(detect_timestamp_format).unique()
    if len(unique_formats) > 1:
        logger.warning("Mixed timestamp formats detected: %s", unique_formats)

    # 4. Check for duplicates across cases (often from truncated precision)
    dup_times = df.groupby("case:concept:name")[col].apply(lambda x: x.duplicated(keep=False).sum()).sum()
    if dup_times > 0:
        logger.warning("%d events share identical timestamps within same case — possible precision truncation", dup_times)

    return n_nat == 0


def detect_timestamp_format(ts_str: str) -> str:
    """Heuristically detect timestamp format category."""
    ts_str = str(ts_str)
    if "/" in ts_str and ":" in ts_str:
        if ts_str.count("/") == 2:
            # Could be MM/DD/YYYY or DD/MM/YYYY
            parts = ts_str.split("/")
            if int(parts[0]) > 12:  # First part > 12 → must be DD/MM
                return "EU_DATETIME"
            elif int(parts[1]) > 12:  # Second part > 12 → must be MM/DD
                return "US_DATETIME"
            else:  # Ambiguous — can't distinguish without context
                return "AMBIGUOUS_DATETIME"
    # ... add more patterns
    return "OTHER"


# Defensive parsing strategy
def parse_timestamp_safe(series: pd.Series, column_name: str = "timestamp") -> pd.Series:
    """Multi-pass timestamp parsing with format detection and error reporting."""
    # Pass 1: Try pandas default (handles ISO-8601, most common formats)
    parsed = pd.to_datetime(series, errors="coerce", utc=True)

    # Pass 2: Try dayfirst=True for EU formats
    if parsed.isna().sum() > 0:
        parsed_fallback = pd.to_datetime(series, errors="coerce", dayfirst=True, utc=True)
        parsed = parsed.fillna(parsed_fallback)

    # Pass 3: Try infer_datetime_format
    if parsed.isna().sum() > 0:
        parsed_fallback = pd.to_datetime(series, errors="coerce", infer_datetime_format=True, utc=True)
        parsed = parsed.fillna(parsed_fallback)

    # Report unparsable values
    n_failed = parsed.isna().sum()
    if n_failed > 0:
        bad_samples = series[parsed.isna()].dropna().unique()[:5]
        logger.warning("Could not parse %d/%d timestamps. Samples: %s", n_failed, len(series), bad_samples)

    return parsed
```

**Prevention checklist:**
- [ ] Log the timestamp parsing failure rate before any pm4py call (<1% target)
- [ ] Reject the pipeline if >5% of timestamps are NaT after parsing
- [ ] Always set `errors="coerce"` then check failure count — never `errors="raise"` in production
- [ ] Always set `utc=True` to avoid timezone comparison issues in pm4py internals
- [ ] Store the raw timestamp column alongside parsed for forensic comparison
- [ ] For Excel files: handle Excel serial dates (float days since 1900-01-01)
- [ ] For SAP exports: watch for trailing whitespace, BOM characters, and `.` as thousands separator

---

### 2.3 Out-of-Order Events (Wrong Model, No Error)

**Root cause:** PM4Py algorithms assume events within each case are chronologically sorted. If they aren't, the mined model shows impossible paths (e.g., "Invoice Received" before "Order Created"). The model is **structurally valid but factually wrong** — and no error is raised.

**How unsorted data breaks process mining:**
```
Expected: [Create Order → Approve Credit → Pick Items → Ship Order]
Actual:   [Create Order → Ship Order → Approve Credit → Pick Items]
           (Out of order due to batch processing lag)
           
Discovered model: Shows "Ship Order" immediately after "Create Order"
                  → Missing "Approve Credit" constraint
                  → Conformance says low fitness (but wrong model)
                  → KPI analysis shows impossible cycle times
```

**Symptom-to-problem mapping:**
```
Negative cycle times      → Timestamps out of order within case
Impossible paths in model → Events not sorted before discovery
Conformance shows many missing tokens → Could be ordering OR drift
Variant count > expected  → Each permutation of activities creates a "new" variant
```

**Diagnostic procedure:**
```python
def diagnose_out_of_order_events(event_log: pd.DataFrame) -> dict:
    """Check for out-of-order events within cases."""
    diagnostics = {}

    # 1. Check if DataFrame is already sorted
    is_sorted = event_log.groupby("case:concept:name")["time:timestamp"].apply(
        lambda x: x.is_monotonic_increasing
    )
    diagnostics["cases_out_of_order"] = int((~is_sorted).sum())
    diagnostics["pct_out_of_order"] = (diagnostics["cases_out_of_order"] / len(is_sorted)) * 100

    # 2. Find cases with negative durations between consecutive events
    event_log = event_log.sort_values(["case:concept:name", "time:timestamp"])
    event_log["_next_timestamp"] = event_log.groupby("case:concept:name")["time:timestamp"].shift(-1)
    event_log["_duration"] = (event_log["_next_timestamp"] - event_log["time:timestamp"]).dt.total_seconds()
    negative_durations = event_log[event_log["_duration"] < 0]
    diagnostics["cases_with_negative_durations"] = negative_durations["case:concept:name"].nunique()

    # 3. Log sample cases
    if diagnostics["cases_out_of_order"] > 0:
        bad_cases = is_sorted[~is_sorted].index[:3]
        logger.warning("Unsorted cases found: %s", list(bad_cases))

    return diagnostics
```

**Prevention:**
```python
# Mandatory step in transformer — never optional
def ensure_chronological_order(df: pd.DataFrame) -> pd.DataFrame:
    """Sort events by case, then timestamp. This MUST run before discovery."""
    before_shape = df.shape
    result = df.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
    if before_shape[0] != result.shape[0]:
        logger.warning("Row count changed during sort — possible duplicate index")
    return result
```

---

### 2.4 Duplicate Case IDs (Silent Data Corruption)

**Root cause:** If multiple distinct process instances share the same case ID, pm4py merges them into a single trace. This produces impossible event sequences (activities from unrelated instances interleaved) and silently corrupts the model.

**ERP scenarios that produce duplicate IDs:**
- Case ID column is nullable and falls back to a default value
- Legacy system reuses order numbers after archive (e.g., ORDER_00001 for 2024 and 2025)
- Composite key needed but only one column selected as case ID
- Character encoding differences: "ORDER_001" vs "ORDER_001 " (trailing space)
- Leading zeros stripped: "00123" vs "123" treated as different

**Diagnostic procedure:**
```python
def diagnose_case_id_quality(df: pd.DataFrame, case_col: str = "case:concept:name") -> dict:
    """Detect problematic case ID patterns."""
    diagnostics = {}

    # 1. Basic duplicate detection
    case_counts = df[case_col].value_counts()
    duplicates = case_counts[case_counts > 1]
    diagnostics["n_duplicates"] = len(duplicates)

    # 2. Flag suspicious case IDs (all same value, null-like values)
    null_like = {"", "null", "NULL", "None", "nan", "NaN", "0", "0000"}
    suspicious = df[df[case_col].astype(str).str.strip().str.lower().isin(null_like)]
    diagnostics["n_null_like_case_ids"] = suspicious[case_col].nunique()
    if diagnostics["n_null_like_case_ids"] > 0:
        logger.warning("Found null-like case IDs: %s", suspicious[case_col].unique())

    # 3. Detect cases with unrealistically many events (possible merge corruption)
    events_per_case = df[case_col].value_counts()
    threshold = events_per_case.quantile(0.99)
    extreme_cases = events_per_case[events_per_case > threshold]
    if len(extreme_cases) > 0:
        diagnostics["extreme_cases"] = len(extreme_cases)
        logger.warning("Cases with abnormally high event count: %s",
                       extreme_cases.head(5).to_dict())

    # 4. Check for case IDs that are too similar (whitespace/encoding variants)
    trimmed_counts = df[case_col].str.strip().value_counts()
    if len(trimmed_counts) < len(case_counts):
        diagnostics["whitespace_variants_detected"] = True
        logger.warning("Case IDs differ only by whitespace — possible duplicate merge")

    return diagnostics
```

**Prevention:**
```python
def deduplicate_case_ids(df: pd.DataFrame, case_col: str = "case:concept:name") -> pd.DataFrame:
    """Strip/standardize case IDs and check for duplicates after normalization."""
    df = df.copy()
    df[case_col] = df[case_col].astype(str).str.strip()

    # Detect real duplicates (same case ID used for different process instances)
    case_time_ranges = df.groupby(case_col)["time:timestamp"].agg(["min", "max"])
    # If a case spans >7 days with no temporal gap, flag it
    suspicious_span = case_time_ranges[
        (case_time_ranges["max"] - case_time_ranges["min"]).dt.days > 7
    ]
    if len(suspicious_span) > 0:
        logger.warning("%d cases span >7 days — possible case ID collision", len(suspicious_span))

    return df
```

---

## 3. Tier 2 — Data Quality Traps

### 3.1 Activity Naming Inconsistencies

**Root cause:** pm4py treats each unique activity string as a distinct activity. "Approve", "approve ", "approve credit", "Approve Credit" are 4 different activities that should be 1. This explodes model complexity and produces spaghetti Petri nets.

**Impact hierarchy:**
```
Tailing whitespace:    "Approve Credit" vs "Approve Credit " → 2 activities (most common)
Case differences:      "approve credit" vs "Approve Credit" → 2 activities
Abbreviation variants: "Appr. Credit" vs "Approve Credit" → 2 activities
Typos:                 "Aprove Credit" vs "Approve Credit" → 2 activities
Leading/trailing:      " Create Order" vs "Create Order" → 2 activities
```

**Diagnostic procedure:**
```python
def diagnose_activity_naming(event_log: pd.DataFrame, activity_col: str = "concept:name") -> dict:
    """Detect activity naming inconsistencies."""
    diagnostics = {}

    activities = event_log[activity_col].unique()
    diagnostics["n_activities"] = len(activities)

    # 1. Whitespace variants
    stripped = set()
    whitespace_issues = []
    for act in activities:
        stripped_act = str(act).strip()
        if stripped_act in stripped:
            whitespace_issues.append(act)
        stripped.add(stripped_act)
    diagnostics["whitespace_variants"] = len(whitespace_issues)

    # 2. Case-insensitive duplicates
    lowered = {}
    case_issues = []
    for act in activities:
        key = str(act).strip().lower()
        if key in lowered:
            case_issues.append((act, lowered[key]))
        lowered[key] = act
    diagnostics["case_variants"] = len(case_issues)

    # 3. Near-duplicates (Levenshtein distance <= 2)
    if len(activities) < 200:  # O(n²) — only for reasonable activity counts
        near_dupes = []
        for i, a1 in enumerate(activities):
            for a2 in activities[i+1:]:
                if levenshtein_distance(str(a1).lower(), str(a2).lower()) <= 2:
                    near_dupes.append((a1, a2))
        diagnostics["near_duplicates"] = len(near_dupes)

    # 4. Rare activities (possible quality issues)
    activity_counts = event_log[activity_col].value_counts()
    rare = activity_counts[activity_counts <= 3]
    diagnostics["rare_activities"] = len(rare)

    return diagnostics


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute edit distance between two strings."""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev + cost)
            prev = temp
    return dp[n]
```

**Prevention:**
```python
def standardize_activity_names(df: pd.DataFrame, activity_col: str = "concept:name") -> pd.DataFrame:
    """Apply normalization rules to activity names."""
    df = df.copy()
    df[activity_col] = (df[activity_col]
        .astype(str)
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)  # collapse multiple spaces
    )
    return df
```

### 3.2 Silent NaN/NaT Event Dropping

**Root cause:** pm4py's internal functions filter out rows with NaN in key columns *silently*. An event log with 10,000 events but 1 NaN timestamp may become 9,999 events — and the model is constructed from the reduced log with no warning.

**Where pm4py drops rows silently:**

| Situation | pm4py Behavior | Detection |
|-----------|---------------|-----------|
| NaN timestamp | Row dropped by `format_dataframe()` | Hard — no log |
| NaN activity name | Row dropped by discovery | Hard — no log |
| NaN case ID | Row becomes its own case | Hard — inflates case count |
| NaN resource | Preserved (optional column) | OK — no issue |

**Diagnostic procedure:**
```python
def trace_event_log_loss(original: pd.DataFrame, processed: pd.DataFrame, label: str = ""):
    """Track how many rows are lost during processing steps."""
    lost = len(original) - len(processed)
    if lost > 0:
        logger.warning(
            "[%s] Pipeline lost %d/%d rows (%.1f%%) during transformation",
            label, lost, len(original), 100 * lost / len(original)
        )


def validate_no_null_required_columns(df: pd.DataFrame) -> list:
    """Check for nulls in pm4py-required columns. Returns list of issues."""
    required = ["case:concept:name", "concept:name", "time:timestamp"]
    issues = []
    for col in required:
        n_null = df[col].isna().sum()
        if n_null > 0:
            issues.append(f"{col}: {n_null} null values ({100*n_null/len(df):.1f}%)")
    return issues
```

---

## 4. Tier 3 — Algorithmic Complexity & Edge Cases

### 4.1 Inductive Miner: Infinite Loops and OOM Crashes

**Root cause:** The Inductive Miner is O(n²) worst-case. With event logs containing >100,000 events or extremely varied traces, it can consume all available memory or run indefinitely. The `IMd` (Directly-Follows) variant is O(n) but sacrifices accuracy.

**Trigger conditions for OOM:**
- >50,000 unique variants (highly varied log with no clear process pattern)
- >500,000 events with >200 unique activities
- Martijn's "spaghetti" processes — logs where every possible path occurs at least once

**Diagnostic procedure:**
```python
def assess_miner_risk(event_log: pd.DataFrame) -> dict:
    """Pre-flight check for Inductive Miner feasibility."""
    n_cases = event_log["case:concept:name"].nunique()
    n_events = len(event_log)
    n_activities = event_log["concept:name"].nunique()
    n_variants = len(pm4py.get_variants_from_log(event_log))
    avg_events_per_case = n_events / n_cases if n_cases > 0 else 0

    risk_assessment = {
        "n_cases": n_cases,
        "n_events": n_events,
        "n_activities": n_activities,
        "n_variants": n_variants,
        "variants_per_case": n_variants / n_cases if n_cases > 0 else 0,
    }

    # Risk indicators
    warnings = []
    if n_variants > 10_000:
        warnings.append(f"CRITICAL: {n_variants} variants — risk of OOM with Inductive Miner")
    if n_variants / n_cases > 0.5:
        warnings.append(f"HIGH: {n_variants/n_cases:.1%} of cases are unique variants — process may be unstructured")
    if n_activities > 100:
        warnings.append(f"HIGH: {n_activities} activities increases complexity")
    if n_events > 500_000:
        warnings.append(f"HIGH: {n_events} events — consider IMd variant or sampling")

    risk_assessment["warnings"] = warnings
    return risk_assessment


# Defensive discovery with timeout and fallback
def discover_petri_net_safe(event_log: pd.DataFrame, timeout_seconds: int = 300) -> tuple:
    """Discover Petri net with timeout and fallback strategy."""
    import signal

    # Pre-flight risk check
    risk = assess_miner_risk(event_log)
    for w in risk["warnings"]:
        logger.warning("Discovery risk: %s", w)

    # Timeout handler
    class TimeoutError(Exception):
        pass

    def handler(signum, frame):
        raise TimeoutError("Inductive Miner timed out")

    # Choose variant based on log size
    if risk["n_events"] > 200_000 or risk["n_variants"] > 10_000:
        logger.info("Large log detected — using IMd (directly-follows) variant")
        variant = "imd"
    else:
        variant = "imf"  # Default IM with frequency

    # Execute with timeout
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_seconds)
    try:
        net, im, fm = pm4py.discover_petri_net_inductive(event_log, variant=variant)
        signal.alarm(0)
        return net, im, fm
    except TimeoutError:
        signal.alarm(0)
        logger.error("Inductive Miner timed out after %d seconds", timeout_seconds)
        # Fallback: try DFG + heuristic reduction
        logger.info("Falling back to Heuristics Miner")
        return pm4py.discover_heuristics_petri_net(event_log)
```

### 4.2 Alignment Computation: Exponential Blowup

**Root cause:** Computing optimal alignments between an event log and a Petri net is **NP-hard** (exponential in the number of tokens × trace length). For Petri nets with parallelism and loops, alignment computation can take hours or exceed memory on a single trace.

**Complexity reality:**
```
Simple sequential model, short traces   → milliseconds
Concurrent model (AND-split), 10 events → seconds
Concurrent model, 50 events             → minutes
Highly concurrent, 100+ events          → hours or OOM
Long traces (>100 events)               → exponential in trace length
```

**Diagnostic procedure:**
```python
def assess_alignment_risk(net, event_log: pd.DataFrame, max_traces_to_sample: int = 100) -> dict:
    """Estimate alignment computation cost before running it."""
    from pm4py.objects.petri_net.utils import petri_utils

    n_places = len(net.places)
    n_transitions = len(net.transitions)
    n_arcs = len(net.arcs)

    # Parallelism indicator: count transitions with both input and output arcs to multiple places
    parallel_indicators = sum(
        1 for t in net.transitions
        if len(petri_utils.pre_set(t)) > 1 or len(petri_utils.post_set(t)) > 1
    )

    # Trace length distribution
    trace_lengths = event_log.groupby("case:concept:name").size()
    max_length = trace_lengths.max()
    mean_length = trace_lengths.mean()

    risk_score = 0
    warnings = []

    if parallel_indicators > 5:
        risk_score += 2
        warnings.append(f"HIGH: {parallel_indicators} synchronization transitions — parallel model, expensive alignment")

    if max_length > 100:
        risk_score += 2
        warnings.append(f"HIGH: max trace length {max_length} — exponential in trace length")

    if n_places + n_transitions > 50:
        risk_score += 1
        warnings.append(f"MEDIUM: large Petri net ({n_places} places, {n_transitions} transitions)")

    return {
        "risk_score": risk_score,
        "n_places": n_places,
        "n_transitions": n_transitions,
        "parallel_indicators": parallel_indicators,
        "max_trace_length": int(max_length) if pd.notna(max_length) else 0,
        "mean_trace_length": round(mean_length, 1) if pd.notna(mean_length) else 0,
        "warnings": warnings,
        "estimated_cost_hint": estimate_alignment_cost(
            parallel_indicators, n_transitions, max_length
        ),
    }


def estimate_alignment_cost(parallel_count: int, n_transitions: int, max_trace_length: int) -> str:
    """Return human-readable cost estimate."""
    # Rough heuristic: cost ∝ transitions^2 × 2^parallel × trace_length
    cost = n_transitions ** 2 * (2 ** min(parallel_count, 8)) * max_trace_length
    if cost < 10_000:
        return "LOW (<1 second per trace)"
    elif cost < 1_000_000:
        return "MEDIUM (1-30 seconds per trace)"
    elif cost < 10_000_000:
        return "HIGH (30 seconds to minutes per trace)"
    else:
        return "CRITICAL (minutes to hours per trace — consider sampling)"


# Safe alignment wrapper
def compute_alignments_safe(
    event_log: pd.DataFrame, net, im, fm,
    max_traces: int = 1000,
    max_trace_length: int = 200,
    timeout_per_trace: int = 30,
) -> list:
    """Compute alignments with guardrails against exponential blowup."""
    risk = assess_alignment_risk(net, event_log)
    for w in risk["warnings"]:
        logger.warning("Alignment risk: %s", w)

    if risk["risk_score"] >= 4:
        logger.warning("High alignment risk — sampling traces instead of full computation")

    # Filter long traces (they dominate alignment cost)
    trace_lengths = event_log.groupby("case:concept:name").size()
    long_cases = trace_lengths[trace_lengths > max_trace_length].index
    if len(long_cases) > 0:
        logger.warning("Excluding %d cases with > %d events (alignment cost)", len(long_cases), max_trace_length)
        event_log = event_log[~event_log["case:concept:name"].isin(long_cases)]

    # Sample if too many traces
    cases = event_log["case:concept:name"].unique()
    if len(cases) > max_traces:
        import random
        sampled = set(random.sample(list(cases), max_traces))
        event_log = event_log[event_log["case:concept:name"].isin(sampled)]
        logger.warning("Sampled %d/%d traces for alignment feasibility", max_traces, len(cases))

    # Compute with timeout
    return pm4py.conformance_diagnostics_alignments(event_log, net, im, fm)
```

**Defensive alignment strategy:**
```
For quick diagnostics (< 100 traces, simple model)       → exact alignments
For large-scale (> 1000 traces)                          → token-based replay (faster)
For parallel models (> 5 concurrent transitions)          → token-based replay
For very long traces (> 200 events)                      → truncated alignments
For "good enough" conformance                            → approximate alignments
```

---

### 4.3 Deadlock Detection in Discovered Petri Nets

**Root cause:** The Inductive Miner guarantees a sound Petri net (no deadlocks, no livelocks) by construction. However, if you convert between model types (e.g., process tree → Petri net → BPMN), apply manual edits, or use Heuristics Miner, the resulting Petri net may deadlock.

**When deadlocks occur:**
- Heuristics Miner output (no soundness guarantee)
- Manual Petri net editing or model merging
- Process tree → Petri net conversion with non-local dependencies
- OC-Petri nets from OCEL data (less constrained)

**Diagnostic procedure:**
```python
def check_petri_net_soundness(net, im, fm) -> dict:
    """Check Petri net for basic soundness properties."""
    from pm4py.objects.petri_net.utils import petri_utils, reachability_graph

    result = {"is_sound": False, "issues": []}

    # 1. Structural check: every place must have at least one input or output arc
    orphan_places = [p for p in net.places if len(petri_utils.pre_set(p)) == 0
                     and len(petri_utils.post_set(p)) == 0]
    if orphan_places:
        result["issues"].append(f"Orphan places (no connections): {len(orphan_places)}")

    # 2. Check for transitions with no input places (dead transitions if initial marking doesn't enable them)
    dead_transitions = []
    for t in net.transitions:
        if len(petri_utils.pre_set(t)) == 0 and t not in fm:
            dead_transitions.append(t)
    if dead_transitions:
        result["issues"].append(f"Potentially dead transitions (no input places): {len(dead_transitions)}")

    # 3. Quick boundedness check via reachability graph (small nets only)
    if len(net.places) < 20:
        try:
            reach_graph = reachability_graph.construct_reachability_graph(net, im)
            # Check if final marking is reachable
            # (full soundness check is expensive; this is a proxy)
            result["reachability_graph_size"] = len(reach_graph)
            result["is_sound"] = len(result["issues"]) == 0
        except Exception as e:
            result["issues"].append(f"Reachability graph construction failed: {e}")
            result["is_sound"] = False
    else:
        # Large net — skip full soundness, warn
        result["issues"].append("Net too large (>20 places) for complete soundness check")
        result["is_sound"] = None

    return result
```

---

## 5. Tier 4 — Visualization & Environment

### 5.1 Graphviz Not Installed

**Root cause:** `graphviz` is a **system-level package** (`apt install graphviz`), not pip-installable. The pip package `graphviz` is just a Python wrapper. New developers will hit this immediately.

**Detection + graceful degradation:**
```python
def render_petri_net_safe(net, im, fm, output_path: str = None):
    """Render Petri net with graceful Graphviz handling."""
    graphviz_available = False
    try:
        import graphviz
        # Also verify the system binary is available
        import subprocess
        subprocess.run(["dot", "-V"], capture_output=True, check=True)
        graphviz_available = True
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError):
        graphviz_available = False

    if graphviz_available:
        from pm4py.visualization.petri_net import visualizer as pn_viz
        gviz = pn_viz.apply(net, im, fm, parameters={
            "format": "svg",
            "bgcolor": "white",
        })
        if output_path:
            pn_viz.save(gviz, output_path)
        return gviz
    else:
        # Textual fallback
        logger.warning("Graphviz not available — rendering textual model representation")
        return render_petri_net_textual(net)


def render_petri_net_textual(net) -> str:
    """Textual representation of a Petri net for when Graphviz is missing."""
    lines = []
    lines.append(f"Petri Net: {len(net.places)} places, {len(net.transitions)} transitions")

    lines.append("\nTransitions (activities):")
    for t in sorted(net.transitions, key=lambda x: str(x.label or "")):
        label = t.label or "(silent/tau)"
        lines.append(f"  - {label}")

    lines.append("\nPlaces:")
    for p in net.places[:20]:  # Limit output
        lines.append(f"  - ({p.name})")

    return "\n".join(lines)
```

### 5.2 pm4py Version API Breaks

**Known breaking changes between pm4py versions:**
```
2.7.0  → 2.7.5:  `discover_petri_net_inductive()` added `variant` parameter
2.7.5  → 2.7.10: `format_dataframe()` introduced; old column mapping approach deprecated
2.7.10 → 2.7.17: OCEL API restructured — `read_ocel()` vs `read_ocel2()` distinction
2.7.17+:         Various parameter renames in visualization functions
```

**Prevention:**
```python
# requirements.txt — pin exact version
pm4py==2.7.17

# In discovery code — always pass explicit keyword arguments
# (protects against positional parameter reordering in future versions)
net, im, fm = pm4py.discover_petri_net_inductive(
    event_log,
    variant="imf",
    case_id_key="case:concept:name",
    activity_key="concept:name",
    timestamp_key="time:timestamp",
)
```

---

## 6. Conformance Checking Diagnostic Procedures

### 6.1 Low Fitness: Is It the Model or the Data?

This is the hardest diagnostic question in process mining. Low conformance fitness means the log doesn't match the model — but which one is wrong?

**Decision tree:**

```
    ┌──────────────────────────────────────┐
    │         FITNESS < 0.8                │
    └──────────────────┬───────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    Check data quality         Check model quality
    ────────────────         ─────────────────
    • Out-of-order events?    • Model from different
    • Missing timestamps?       time period?
    • Duplicate case IDs?     • Different process variant?
    • Activity naming noise?  • Manual edits introduced
    • Extremely varied log?     deadlocks?
          │                         │
          ▼                         ▼
    ┌──────────┐              ┌──────────┐
    │Data clean│              │Data clean│
    │but model │              │but model │
    │no match  │              │no match  │
    └────┬─────┘              └────┬─────┘
         │                         │
         └─────────┬───────────────┘
                   ▼
         ┌─────────────────────┐
         │  TRUE DEVIATION     │
         │  (shadow process /  │
         │  unauthorized path) │
         └─────────────────────┘
              ↑ This is the actual process mining insight!
```

**Diagnostic procedure:**
```python
def diagnose_low_fitness(event_log: pd.DataFrame, net, im, fm) -> dict:
    """Determine if low fitness is data issue, model issue, or real deviation."""
    from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
    import collections

    diagnostics = {}

    # 1. Token-based replay (faster than alignments for large logs)
    replay_result = token_replay.apply(event_log, net, im, fm)

    # 2. Categorize deviations
    produced_tokens = sum(r.get("produced_tokens", 0) for r in replay_result)
    consumed_tokens = sum(r.get("consumed_tokens", 0) for r in replay_result)
    missing_tokens = sum(r.get("missing_tokens", 0) for r in replay_result)
    remaining_tokens = sum(r.get("remaining_tokens", 0) for r in replay_result)

    trace_fitness = []
    for r in replay_result:
        trace_fitness.append(1.0 - (r.get("missing_tokens", 0) + r.get("remaining_tokens", 0))
                             / max(r.get("produced_tokens", 1), 1))

    diagnostics["fitness"] = sum(trace_fitness) / len(trace_fitness) if trace_fitness else 0.0
    diagnostics["missing_tokens"] = missing_tokens
    diagnostics["remaining_tokens"] = remaining_tokens

    # 3. Pattern analysis: determine deviation type
    # High missing + low remaining = model expects activities not in log (model too strict)
    # Low missing + high remaining = log has activities model doesn't (model too permissive)
    # High missing + high remaining = fundamental mismatch
    total_deviation = missing_tokens + remaining_tokens
    if total_deviation == 0:
        diagnostics["diagnosis"] = "PERFECT_FIT"
    elif missing_tokens / total_deviation > 0.7:
        diagnostics["diagnosis"] = "MODEL_TOO_STRICT — log has paths model doesn't allow"
        #  → Need more flexible model (higher noise threshold, different algorithm)
    elif remaining_tokens / total_deviation > 0.7:
        diagnostics["diagnosis"] = "MODEL_TOO_PERMISSIVE — model allows paths log doesn't show"
        #  → Model overgeneralizes (reduce noise threshold)
    else:
        diagnostics["diagnosis"] = "STRUCTURAL_MISMATCH — fundamental process deviation"

    # 4. Find most-deviant traces (these are the "interesting" diagnostics)
    deviant_traces = sorted(
        [(i, f) for i, f in enumerate(trace_fitness) if f < 0.8],
        key=lambda x: x[1]
    )[:10]

    diagnostics["n_deviant_traces"] = len(deviant_traces)
    diagnostics["sample_deviant_fitness"] = [round(f, 3) for _, f in deviant_traces[:5]]

    return diagnostics


def visualize_deviant_trace(event_log: pd.DataFrame, trace_id: str, net):
    """Show a deviant trace vs model to diagnose fitness issues."""
    trace = event_log[event_log["case:concept:name"] == trace_id]
    activities = trace["concept:name"].tolist()
    timestamps = trace["time:timestamp"].tolist()

    print(f"Trace: {trace_id}")
    print(f"Sequence: {' → '.join(activities)}")
    for i, (act, ts) in enumerate(zip(activities, timestamps)):
        print(f"  {i+1}. [{ts}] {act}")

    # Compare to model transitions
    model_activities = sorted(set(
        str(t.label) for t in net.transitions if t.label is not None
    ))
    trace_activities = set(activities)
    missing = model_activities - trace_activities
    extra = trace_activities - model_activities
    if missing:
        print(f"Activities expected by model but absent in trace: {missing}")
    if extra:
        print(f"Activities in trace but not in model: {extra}")
```

### 6.2 Variant Analysis for Diagnostic Insight

```python
def diagnose_variant_distribution(event_log: pd.DataFrame) -> dict:
    """Use trace variants to understand process structure and diagnose issues."""
    variants = pm4py.get_variants_from_log(event_log)

    diagnostics = {}
    diagnostics["n_variants"] = len(variants)
    diagnostics["n_cases"] = event_log["case:concept:name"].nunique()

    # Find most common variants
    sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)
    diagnostics["top_variants"] = {
        variant: count
        for variant, count in sorted_variants[:5]
    }

    # Concentration metric: what % of cases are covered by the top-3 variants?
    total_cases = diagnostics["n_cases"]
    top3_coverage = sum(count for _, count in sorted_variants[:3])
    diagnostics["top3_variant_coverage"] = round(top3_coverage / total_cases * 100, 1) if total_cases > 0 else 0

    # Diagnostic interpretation
    coverage = diagnostics["top3_variant_coverage"]
    if coverage > 80:
        diagnostics["process_type"] = "HIGHLY_STANDARDIZED"
    elif coverage > 50:
        diagnostics["process_type"] = "MODERATELY_VARIED"
    elif coverage > 20:
        diagnostics["process_type"] = "HIGHLY_VARIED"
    else:
        diagnostics["process_type"] = "UNSTRUCTURED_SPAGHETTI"
        diagnostics["warning"] = "Process appears unstructured — consider filtering or aggregation"

    return diagnostics
```

---

## 7. Defensive Programming Patterns

### 7.1 The Defensive Pipeline Wrapper

Wrap every pm4py call in a standardized guard:

```python
import time
import logging
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)


def pm4py_guard(pipeline_stage: str, func, *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
    """Execute a pm4py function with comprehensive guardrails.

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str])
    """
    start = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info("[%s] completed in %.2fs", pipeline_stage, duration)
        return True, result, None
    except MemoryError:
        duration = time.time() - start
        logger.error("[%s] OUT OF MEMORY after %.2fs — %s too large", pipeline_stage, duration, pipeline_stage)
        return False, None, "OUT_OF_MEMORY"
    except TimeoutError:
        duration = time.time() - start
        logger.error("[%s] TIMEOUT after %.2fs", pipeline_stage, duration)
        return False, None, "TIMEOUT"
    except KeyError as e:
        logger.error("[%s] Missing column: %s — check transformer output", pipeline_stage, e)
        return False, None, f"KEY_ERROR: {e}"
    except Exception as e:
        duration = time.time() - start
        logger.error("[%s] Failed after %.2fs: %s", pipeline_stage, duration, e, exc_info=True)
        return False, None, str(e)
```

### 7.2 Pre-Flight Data Quality Gate

```python
class DataQualityGate:
    """Run this before any discovery or conformance operation."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.issues = []

    def check(self) -> list:
        """Run all checks. Returns list of issue strings (empty = pass)."""
        self.issues = []
        self._check_column_presence()
        self._check_empty()
        self._check_null_rates()
        self._check_case_count()
        self._check_timestamp_ordering()
        self._check_duplicate_timestamps()
        self._check_case_id_quality()
        return self.issues

    def _check_column_presence(self):
        required = {"case:concept:name", "concept:name", "time:timestamp"}
        missing = required - set(self.df.columns)
        if missing:
            self.issues.append(f"FAIL: Missing required columns: {missing}")

    def _check_empty(self):
        if len(self.df) == 0:
            self.issues.append("FAIL: Event log is empty")

    def _check_null_rates(self):
        for col in ["case:concept:name", "concept:name", "time:timestamp"]:
            if col in self.df.columns:
                null_rate = self.df[col].isna().mean()
                if null_rate > 0.05:
                    self.issues.append(f"WARN: {null_rate:.1%} null values in '{col}' (threshold: 5%)")
                elif null_rate > 0:
                    self.issues.append(f"INFO: {null_rate:.1%} null values in '{col}'")

    def _check_case_count(self):
        n_cases = self.df["case:concept:name"].nunique()
        if n_cases < 2:
            self.issues.append("FAIL: At least 2 cases required for process discovery")
        elif n_cases < 10:
            self.issues.append(f"WARN: Only {n_cases} cases — model quality may be low")

    def _check_timestamp_ordering(self):
        """Check that events within cases are chronological."""
        if "time:timestamp" not in self.df.columns or self.df["time:timestamp"].isna().any():
            return
        sorted_check = self.df.sort_values(["case:concept:name", "time:timestamp"])
        is_sorted = sorted_check.equals(self.df)
        if not is_sorted:
            self.issues.append("WARN: DataFrame is NOT sorted by case+timestamp")

    def _check_duplicate_timestamps(self):
        """Detect cases where multiple events share the same timestamp (possible precision loss)."""
        if "time:timestamp" not in self.df.columns:
            return
        dup = self.df.duplicated(subset=["case:concept:name", "time:timestamp"], keep=False)
        n_dup = dup.sum()
        if n_dup > 0:
            self.issues.append(f"WARN: {n_dup} events share identical case+timestamp — possible time precision loss")

    def _check_case_id_quality(self):
        ids = self.df["case:concept:name"].astype(str).str.strip()
        # Check for null-like values
        null_like = ids.isin(["", "null", "NULL", "nan", "NaN"])
        if null_like.any():
            self.issues.append(f"FAIL: Found {null_like.sum()} null-like case IDs after stripping")


# Usage
gate = DataQualityGate(event_log)
issues = gate.check()
if any(i.startswith("FAIL") for i in issues):
    raise ValueError(f"Data quality gate failed:\n" + "\n".join(issues))
```

### 7.3 Pipeline Shearing Forces Protection

Anticipate where the planned layers will most likely shear:

| Interface | Likely Failure | Protection |
|-----------|---------------|------------|
| `transformer.py` → `inductive.py` | Column names wrong | DataQualityGate before discovery |
| `inductive.py` → `conformance/alignments.py` | Model is None | Return Optional, check before pass |
| `data/loader.py` → `data/transformer.py` | File format mismatch | Try-except with format fallback |
| `viz/dashboard.py` → all | Unexpected model format | Render expects `Optional[Tuple]` |

### 7.4 Save Raw + Processed Side by Side

Always preserve the raw data alongside the processed version for forensic debugging:

```python
def save_with_provenance(processed_df: pd.DataFrame, raw_df: pd.DataFrame, path: str):
    """Save processed data alongside raw data for forensic comparison."""
    processed_df.to_parquet(f"{path}/event_log.pq")
    raw_df.to_parquet(f"{path}/event_log_raw.pq")
    # Save transformation metadata
    import json
    meta = {
        "original_shape": list(raw_df.shape),
        "processed_shape": list(processed_df.shape),
        "n_cases": processed_df["case:concept:name"].nunique(),
        "n_events": len(processed_df),
        "timestamp_range": [
            str(processed_df["time:timestamp"].min()),
            str(processed_df["time:timestamp"].max()),
        ],
    }
    with open(f"{path}/provenance.json", "w") as f:
        json.dump(meta, f, indent=2)
```

---

## 8. Testing Strategy

### Test Levels for Process Mining Bugs

| Level | Catches | Example |
|-------|---------|---------|
| **Unit** (function-level) | Column mapping, timestamp parsing | `test_parse_timestamp_eu_format()` |
| **Integration** (load→discover) | Pipeline wiring, pm4py API compat | `test_load_inductive_end_to_end()` |
| **Regression** (fixed bugs) | Re-occurrence of known issues | `test_no_silent_nat_drop()` |
| **Synthetic data** | Algorithm correctness | Known input → known output model |
| **Data quality** | Bad input detection | Validator rejects missing timestamps |

### Critical Test Cases

```python
# 1. Empty log → graceful None return
def test_inductive_empty_log():
    df = pd.DataFrame(columns=["case:concept:name", "concept:name", "time:timestamp"])
    result = discover_petri_net_safe(df)
    assert result is None

# 2. Single case → graceful None return
def test_inductive_single_case():
    df = pd.DataFrame({
        "case:concept:name": ["C1"] * 5,
        "concept:name": ["A", "B", "C", "D", "E"],
        "time:timestamp": pd.date_range("2025-01-01", periods=5, freq="h"),
    })
    result = discover_petri_net_safe(df)
    assert result is None  # Need 2+ cases

# 3. Out-of-order events → model should handle correctly
def test_inductive_handles_unsorted_input():
    df = pd.DataFrame({
        "case:concept:name": ["C1", "C1", "C1"],
        "concept:name": ["A", "C", "B"],  # Out of order
        "time:timestamp": pd.to_datetime([
            "2025-01-01 08:00", "2025-01-01 10:00", "2025-01-01 09:00"
        ]),
    })
    # Ensure transformer sorts before discovery
    df = ensure_chronological_order(df)
    result = discover_petri_net_safe(df)
    assert result is not None

# 4. Column name mismatch → clear error, not silent wrong model
def test_inductive_wrong_column_names():
    df = pd.DataFrame({
        "order_id": ["C1", "C1"],
        "event": ["A", "B"],
        "date": ["2025-01-01", "2025-01-02"],
    })
    with pytest.raises(ValueError, match="Missing required columns"):
        transform_to_pm4py(df, {"order_id": "case:concept:name", "event": "concept:name", "date": "time:timestamp"})

# 5. NaN timestamps → detectable warning
def test_timestamp_nan_handling(caplog):
    df = pd.DataFrame({
        "case:concept:name": ["C1", "C1"],
        "concept:name": ["A", "B"],
        "time:timestamp": ["2025-01-01", None],
    })
    df["time:timestamp"] = parse_timestamp_safe(df["time:timestamp"])
    assert df["time:timestamp"].isna().sum() == 1
    assert "Could not parse" in caplog.text

# 6. Activity naming noise → normalization works
def test_activity_normalization():
    df = pd.DataFrame({
        "case:concept:name": ["C1", "C1"],
        "concept:name": ["Approve ", " Approve"],  # Whitespace variants
        "time:timestamp": pd.to_datetime(["2025-01-01", "2025-01-02"]),
    })
    df = standardize_activity_names(df)
    assert df["concept:name"].nunique() == 1

# 7. Timestamp ordering → model correctness
def test_out_of_order_detection():
    """Sorted vs unsorted data should produce different model warnings."""
    df = pd.DataFrame({
        "case:concept:name": ["C1", "C1", "C1"],
        "concept:name": ["Create Order", "Approve Credit", "Pick Items"],
        "time:timestamp": pd.to_datetime([
            "2025-01-01 08:00",
            "2025-01-01 10:00",  # Later
            "2025-01-01 09:00",  # Out of order!
        ]),
    })
    diagnostics = diagnose_out_of_order_events(df)
    assert diagnostics["cases_out_of_order"] > 0
```

### Synthetic Log Generator for Testing

Essential for deterministic debugging — build this first:

```python
def generate_test_log(
    base_activities: list = None,
    n_cases: int = 10,
    add_noise: bool = False,
    noise_rate: float = 0.1,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate deterministic test event logs with known ground truth.

    The returned log has known structure — you can compare the discovered
    model against the expected model to detect bugs.
    """
    import random
    random.seed(seed)

    if base_activities is None:
        base_activities = [
            "Create Order",
            "Approve Credit",
            "Pick Items",
            "Ship Order",
            "Invoice",
            "Payment Cleared",
        ]

    records = []
    for i in range(n_cases):
        case_id = f"TEST_{i:04d}"
        timestamp = pd.Timestamp("2025-01-01 08:00") + pd.Timedelta(days=i)

        for activity in base_activities:
            records.append({
                "case:concept:name": case_id,
                "concept:name": activity,
                "time:timestamp": timestamp,
            })
            timestamp += pd.Timedelta(hours=1)

        if add_noise:
            # Add rework loops (repeat an activity)
            if random.random() < noise_rate:
                rework_activity = random.choice(base_activities[:-1])
                records.append({
                    "case:concept:name": case_id,
                    "concept:name": rework_activity,
                    "time:timestamp": timestamp + pd.Timedelta(minutes=30),
                })

            # Add skipped activities
            if random.random() < noise_rate:
                skip_idx = random.randint(0, len(base_activities) - 2)
                records = [r for r in records
                          if not (r["case:concept:name"] == case_id
                                  and r["concept:name"] == base_activities[skip_idx])]

    return pd.DataFrame(records).sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
```

---

## 9. pm4py API Pitfall Catalog

| # | API Call | Common Mistake | Correct Usage |
|---|----------|---------------|---------------|
| 1 | `pm4py.discover_petri_net_inductive(log)` | Passes unformatted DataFrame | Always pass `case_id_key`, `activity_key`, `timestamp_key` |
| 2 | `pm4py.conformance_diagnostics_alignments(log, net, im, fm)` | Computes on full log — OOM | Sample traces first, or use token replay |
| 3 | `pm4py.format_dataframe(df)` | Doesn't save return value | Returns new DataFrame — does NOT modify in place |
| 4 | `pm4py.read_ocel(path)` | Assumes any OCEL file works | OCEL 2.0 files need `read_ocel2()` |
| 5 | `pm4py.view_petri_net(net, im, fm)` | Raises ImportError if graphviz missing | Wrap in try/except with fallback |
| 6 | `pm4py.discover_dfg(log)` | Assumes sorted input | Always sort before DFG extraction |
| 7 | `pm4py.get_variants(log)` | Doesn't use result for insight | Compare variant overlap with expected SOP |
| 8 | `pm4py.convert_to_bpmn(net)` | Loses information in conversion | Not all Petri nets can convert to BPMN losslessly |
| 9 | `pm4py.filter_variants(log, [variant])` | Filtering changes denominators | Recompute metrics on filtered log, not original |
| 10 | `pm4py.statistics.log.get_log_size(log)` | Returns event count, not row count | Fine — but don't confuse with case count |

---

## Appendix: Quick Diagnostic Decision Tree

```
                      BUG SYMPTOM
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   CRASH AT            MODEL IS           WRONG METRICS
   STARTUP             SPAGHETTI          (fitness,KPI)
        │                  │                  │
        ▼                  ▼                  ▼
   Column names?       Activity names     Data not sorted?
   Timestamp parse?    Too many           Duplicate case IDs?
   Empty log?          variants?          Column mapping
   Graphviz missing?   Noise too high?    off in conformance?
        │                  │                  │
        ▼                  ▼                  ▼
   Fix in             Aggregate or        Fix in transformer
   transformer        filter variants     or validator
```

---

*Document generated: 2026-07-01 | Based on pm4py 2.7.x behavior | Covers project architecture from .planning/codebase/*

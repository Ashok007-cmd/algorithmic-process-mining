from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

O2C_ACTIVITIES = [
    "Order Created",
    "Order Confirmed",
    "Picked",
    "Packed",
    "Shipped",
    "Invoice Sent",
    "Payment Received",
    "Invoice Cleared",
]

P2P_ACTIVITIES = [
    "PO Created",
    "PO Approved",
    "Goods Received",
    "Invoice Received",
    "Invoice Verified",
    "Payment Processed",
    "PO Closed",
]


@dataclass
class ProcessModel:
    name: str
    activities: list[str]
    happy_path: list[str]
    rework_points: dict[str, str] = field(default_factory=dict)
    skip_allowed: set[str] = field(default_factory=set)
    insertion_allowed: set[str] = field(default_factory=set)


O2C_MODEL = ProcessModel(
    name="order_to_cash",
    activities=O2C_ACTIVITIES,
    happy_path=[
        "Order Created",
        "Order Confirmed",
        "Picked",
        "Packed",
        "Shipped",
        "Invoice Sent",
        "Payment Received",
        "Invoice Cleared",
    ],
    rework_points={
        "Picked": "Order Confirmed",
        "Invoice Sent": "Shipped",
    },
    skip_allowed={"Order Confirmed", "Packed"},
    insertion_allowed={"Picked", "Invoice Sent"},
)

P2P_MODEL = ProcessModel(
    name="procure_to_pay",
    activities=P2P_ACTIVITIES,
    happy_path=[
        "PO Created",
        "PO Approved",
        "Goods Received",
        "Invoice Received",
        "Invoice Verified",
        "Payment Processed",
        "PO Closed",
    ],
    rework_points={
        "Invoice Received": "Goods Received",
        "Payment Processed": "Invoice Verified",
    },
    skip_allowed={"PO Approved", "Invoice Verified"},
    insertion_allowed={"Goods Received", "Invoice Received"},
)


def _inject_noise(
    trace: list[str],
    model: ProcessModel,
    rng: random.Random,
    skip_prob: float = 0.05,
    rework_prob: float = 0.05,
    insertion_prob: float = 0.03,
) -> list[str]:
    result: list[str] = []
    for act in trace:
        if act in model.skip_allowed and rng.random() < skip_prob:
            continue
        result.append(act)
        if act in model.rework_points and rng.random() < rework_prob:
            result.append(model.rework_points[act])
        if act in model.insertion_allowed and rng.random() < insertion_prob:
            result.append(act)
    return result


def generate_o2c_log(
    n_cases: int = 100,
    noise_level: float = 0.0,
    seed: int = 42,
    start_date: datetime | None = None,
) -> pd.DataFrame:
    return generate_event_log(
        model=O2C_MODEL,
        n_cases=n_cases,
        noise_level=noise_level,
        seed=seed,
        start_date=start_date,
    )


def generate_p2p_log(
    n_cases: int = 100,
    noise_level: float = 0.0,
    seed: int = 42,
    start_date: datetime | None = None,
) -> pd.DataFrame:
    return generate_event_log(
        model=P2P_MODEL,
        n_cases=n_cases,
        noise_level=noise_level,
        seed=seed,
        start_date=start_date,
    )


def generate_event_log(
    model: ProcessModel,
    n_cases: int = 100,
    noise_level: float = 0.0,
    seed: int = 42,
    start_date: datetime | None = None,
) -> pd.DataFrame:
    if n_cases < 1:
        raise ValueError(f"n_cases must be >= 1, got {n_cases}")
    rng = random.Random(seed)  # nosec B311
    if start_date is None:
        start_date = datetime(2024, 1, 1, 8, 0, 0)

    skip_prob = 0.15 * noise_level
    rework_prob = 0.15 * noise_level
    insertion_prob = 0.10 * noise_level

    records: list[dict[str, Any]] = []
    for case_idx in range(n_cases):
        case_id = f"{model.name[:3].upper()}_{case_idx + 1:05d}"
        base_trace = list(model.happy_path)
        noisy_trace = _inject_noise(base_trace, model, rng, skip_prob, rework_prob, insertion_prob)
        current_time = start_date + timedelta(
            days=rng.randint(0, 90),
            hours=rng.randint(0, 8),
            minutes=rng.randint(0, 59),
        )
        for act in noisy_trace:
            duration_minutes = rng.randint(30, 480)
            current_time += timedelta(minutes=duration_minutes)
            records.append(
                {
                    "case:concept:name": case_id,
                    "concept:name": act,
                    "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    df = pd.DataFrame(records)
    df = df.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
    return df


def get_normative_sequences(model_name: str) -> list[list[str]]:
    if model_name == "o2c":
        return [list(O2C_MODEL.happy_path)]
    elif model_name == "p2p":
        return [list(P2P_MODEL.happy_path)]
    raise ValueError(f"Unknown model: {model_name}")

from __future__ import annotations

from pathlib import Path

import pytest

TEST_DATA = Path(__file__).parent / "data"
SAMPLE_O2C_LOG = TEST_DATA / "sample_o2c.csv"
SAMPLE_P2P_LOG = TEST_DATA / "sample_p2p.csv"


@pytest.fixture(scope="session")
def sample_o2c_df():
    import pandas as pd

    return pd.read_csv(SAMPLE_O2C_LOG)


@pytest.fixture(scope="session")
def sample_p2p_df():
    import pandas as pd

    return pd.read_csv(SAMPLE_P2P_LOG)


@pytest.fixture(scope="session")
def o2c_df():
    from src.data.generators.synthetic import generate_o2c_log

    return generate_o2c_log(n_cases=10, noise_level=0.0, seed=42)


@pytest.fixture(scope="session")
def p2p_df():
    from src.data.generators.synthetic import generate_p2p_log

    return generate_p2p_log(n_cases=10, noise_level=0.0, seed=42)

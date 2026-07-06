from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import pandas as pd

_F = TypeVar("_F", bound=Callable[..., Any])


def dataframe_hash(df: pd.DataFrame) -> int:
    """Content hash of an event log DataFrame, suitable for use as a cache key."""
    row_hashes = pd.util.hash_pandas_object(df, index=True).to_numpy()
    return hash((row_hashes.tobytes(), tuple(df.columns)))


def cached_discovery(maxsize: int = 4) -> Callable[[_F], _F]:
    """Memoize a discovery/conformance function whose first argument is an event
    log DataFrame.

    DataFrames aren't hashable, so plain `functools.lru_cache` can't be applied
    to functions like `discover_inductive(df, ...)` directly -- this hashes the
    DataFrame's content (via `dataframe_hash`) and the remaining arguments to
    build the cache key instead, with simple LRU eviction.
    """

    def decorator(func: _F) -> _F:
        cache: OrderedDict[tuple[Any, ...], Any] = OrderedDict()

        @wraps(func)
        def wrapper(df: pd.DataFrame, *args: Any, **kwargs: Any) -> Any:
            key = (dataframe_hash(df), args, tuple(sorted(kwargs.items())))
            if key in cache:
                cache.move_to_end(key)
                return cache[key]
            result = func(df, *args, **kwargs)
            cache[key] = result
            if len(cache) > maxsize:
                cache.popitem(last=False)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator

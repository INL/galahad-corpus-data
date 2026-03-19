"""Timer functionality."""

from contextlib import ContextDecorator
from time import perf_counter
from typing import Self


class Timer(ContextDecorator):
    """Context manager that measures elapsed time."""

    def __init__(self, name: str) -> None:
        """Create timer with label used when printing."""
        self.name = name

    def __enter__(self) -> Self:
        """Start timer on context enter."""
        self.start = perf_counter()
        return self

    def __exit__(self, *_) -> None:
        """Stop timer on context exit."""
        print(f"\t{self.name} took {self.elapsed:.2f}s", flush=True)

    @property
    def elapsed(self) -> float:
        """Seconds elapsed since start."""
        return perf_counter() - self.start

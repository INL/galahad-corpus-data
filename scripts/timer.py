from contextlib import ContextDecorator
from time import perf_counter


class Timer(ContextDecorator):
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *_):
        print(f"\t{self.name} took {self.elapsed:.2f}s", flush=True)

    @property
    def elapsed(self) -> float:
        return perf_counter() - self.start

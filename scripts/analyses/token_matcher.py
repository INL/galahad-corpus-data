from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from data import TsvCorpus, TsvWord


@dataclass
class TokenMatcher:
    out: Path
    corpus: TsvCorpus

    def filter(self, condition: Callable[[TsvWord], bool]) -> None:
        """Filter tokens based on a given condition and write to output."""
        with self.out.open("w") as f:
            for w in self.corpus.words:
                if condition(w):
                    f.write(str(w) + "\n")

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from data import TsvCorpus, TsvWord


@dataclass
class TokenFilter:
    out: Path
    corpus: TsvCorpus

    def filter(self, condition: Callable[[TsvWord], bool]) -> None:
        """Filter tokens based on a given condition and write to output."""
        with self.out.open("w") as f:
            for d in self.corpus.dirs:
                written_header = False
                for w in d.words:
                    if condition(w):
                        if not written_header:
                            written_header = True
                            f.write(f"\n{d.name:-^40}\n")
                        f.write(str(w) + "\n")

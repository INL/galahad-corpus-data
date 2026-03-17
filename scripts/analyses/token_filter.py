from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from data import TsvCorpus, TsvWord


@dataclass
class TokenFilter:
    out: Path
    corpus: TsvCorpus

    def filter(
        self,
        condition: Callable[[TsvWord], bool],
        comment: Callable[[TsvWord], str] | None = None,
    ) -> None:
        """Filter tokens based on a given condition and write to output."""
        with self.out.open("w") as f:
            for d in self.corpus.dirs:
                written_header = False
                for w in d.words:
                    if condition(w):
                        if not written_header:
                            written_header = True
                            f.write(f"\n{d.name:-^40}\n")
                        cmt: str = ("\t " + comment(w)) if comment else ""
                        f.write(f"{w}{cmt}\n")

    def report(self, condition: Callable[[TsvWord], bool]) -> None:
        with self.out.open("w", encoding="utf-8") as f:
            for dir in self.corpus.dirs:
                f.write(f"{dir.name:-^60}\n")

                words = list(dir.words)
                for i in range(len(words)):
                    w = words[i]
                    if condition(w):
                        CONTEXT_BEFORE = 10
                        CONTEXT_AFTER = 3
                        start = max(0, i - CONTEXT_BEFORE)
                        end = min(len(words), i + CONTEXT_AFTER + 1)
                        for j in range(start, end):
                            prefix = ">> " if j == i else "   "
                            c = words[j]
                            mwe = "[MWE] " if c.group else "      "
                            word = f"{c.token:<25} {c.lemma:<25} {c.pos}"
                            f.write(f"{prefix}{mwe}{word}\n")
                        f.write("\n\n")

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Tuple

from data import TsvCorpus, TsvWord


@dataclass
class SortedAnalyses:
    analyses: list[Tuple[str, int]]
    total: int

    def __str__(self) -> str:
        return "\n".join(
            f"\t\t\t{count} {count / self.total * 100:>5.1f}% {analysis}"
            for analysis, count in self.analyses
        )

    @staticmethod
    def from_dict(map: dict[str, int]) -> "SortedAnalyses":
        return SortedAnalyses(
            sorted(map.items(), key=(lambda kv: -kv[1])), sum(map.values())
        )


@dataclass
class AnalysesGroup:
    key: str
    mwe: SortedAnalyses
    non_mwe: SortedAnalyses
    total: int

    def __str__(self) -> str:
        s = f"{self.total} {self.key}\n"
        for analysis_type, analyses in [("NON-MWE", self.non_mwe), ("MWE", self.mwe)]:
            if analyses.total == 0:
                continue
            s += f"\t{analyses.total} {analyses.total / self.total * 100:>6.2f}% {analysis_type}\n"
            s += str(analyses) + "\n"
        return s

    @staticmethod
    def from_map(key: str, map: dict[str, dict[str, int]]) -> "AnalysesGroup":
        mwe = SortedAnalyses.from_dict(map.get("[MWE]", {}))
        non_mwe = SortedAnalyses.from_dict(map.get("[NON-MWE]", {}))
        return AnalysesGroup(key, mwe, non_mwe, mwe.total + non_mwe.total)


@dataclass
class TokenGrouper:
    def __init__(
        self,
        out: Path,
        corpus: TsvCorpus,
        key_mapper: Callable[[TsvWord], str],
        value_mapper: Callable[[TsvWord], str],
    ):
        self.key_mapper = key_mapper
        self.value_mapper = value_mapper
        self.groups = self.get_map(corpus, key_mapper, value_mapper)
        out.write_text("\n".join(str(g) for g in self.groups))

    def get_map(
        self,
        corpus: TsvCorpus,
        key_mapper: Callable[[TsvWord], str],
        value_mapper: Callable[[TsvWord], str],
    ) -> list[AnalysesGroup]:
        map: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        for w in corpus.words:
            key = key_mapper(w)
            value = value_mapper(w)
            if w.group:
                map[key]["[MWE]"][value] += 1
            else:
                map[key]["[NON-MWE]"][value] += 1

        return sorted(
            (AnalysesGroup.from_map(k, v) for k, v in map.items()),
            key=lambda x: -x.total,
        )


class SuspiciousTokenGrouper(TokenGrouper):
    def get_map(
        self,
        corpus: TsvCorpus,
        key_mapper: Callable[[TsvWord], str],
        value_mapper: Callable[[TsvWord], str],
    ) -> list[AnalysesGroup]:
        map = super().get_map(corpus, key_mapper, value_mapper)

        for g in map:
            g.non_mwe.analyses = [
                (analysis, count)
                for analysis, count in g.non_mwe.analyses
                if count <= 5 and (count / g.total) <= 0.01
            ]
            g.mwe.total = 0  # ignore MWE entries

        return [g for g in map if len(g.non_mwe.analyses)]

    def is_suspicious(self, w: TsvWord) -> bool:
        if w.group:
            return False
        key = self.key_mapper(w)
        value = self.value_mapper(w)
        for group in self.groups:
            if group.key == key:
                for analysis, count in group.non_mwe.analyses:
                    if analysis == value:
                        return True
        return False

    def report(self, out: Path, corpus: TsvCorpus):
        with out.open("w", encoding="utf-8") as f:
            for dir in corpus.dirs:
                f.write(f"{dir.name:-^60}\n")

                words = list(dir.words)
                for i in range(len(words)):
                    w = words[i]
                    if self.is_suspicious(w):
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

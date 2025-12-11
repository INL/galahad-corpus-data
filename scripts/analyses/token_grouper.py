from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from data import TsvCorpus, TsvWord


@dataclass
class TokenGrouper:
    def __init__(
        self,
        out: Path,
        corpus: TsvCorpus,
        group_by: Callable[[TsvWord], str],
        sort_by: Callable[[TsvWord], str],
    ):
        map: dict[str, dict[str, int]] = {}
        for w in corpus.words:
            key = group_by(w)
            group = map.get(key, {})
            sort_key = sort_by(w)
            group[sort_key] = group.get(sort_key, 0) + 1
            map[key] = group
        with out.open("w") as f:
            for key, group in sorted(map.items(), key=lambda x: -sum(x[1].values())):
                total_count = sum(group.values())
                f.write(f"{total_count} {key}\n")
                for sort_key, count in sorted(
                    group.items(), key=lambda x: (-x[1], x[0])
                ):
                    f.write(f"\t{count:>5} {sort_key}\n")
                f.write("\n")

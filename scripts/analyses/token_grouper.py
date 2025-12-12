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
            if w.group:
                mwe = " ".join([sort_by(mw) for mw in w.mwe])
                sort_key = f" MWE[{mwe}]"

            group[sort_key] = group.get(sort_key, 0) + 1
            map[key] = group
        with out.open("w") as f:
            for key, group in sorted(map.items(), key=lambda x: -sum(x[1].values())):
                total_count = sum(group.values())
                f.write(f"{total_count} {key}\n")

                mwe_items = {}
                non_mwe_items = {}

                for sort_key, count in sorted(
                    group.items(), key=lambda x: (-x[1], x[0])
                ):
                    if "MWE[" in sort_key:
                        mwe_items[sort_key] = count
                    else:
                        non_mwe_items[sort_key] = count

                f.write(f"{sum(non_mwe_items.values())} [NOT-MWE]\n")
                for sort_key, count in non_mwe_items.items():
                    f.write(f"{count:>7}   {sort_key}\n")

                f.write(f"{sum(mwe_items.values())} [MWE]\n")
                for sort_key, count in mwe_items.items():
                    f.write(f"{count:>7}   {sort_key}\n")
                f.write("\n")

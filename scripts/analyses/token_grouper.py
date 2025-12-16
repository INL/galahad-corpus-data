from collections import defaultdict
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
        key_mapper: Callable[[TsvWord], str],
        value_mapper: Callable[[TsvWord], str],
    ):
        map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for w in corpus.words:
            key = key_mapper(w)
            if w.group:
                value = f" MWE[{' '.join([value_mapper(m) for m in w.mwe])}]"
            else:
                value = value_mapper(w)
            map[key][value] += 1

        with out.open("w") as f:
            for key, values in sorted(map.items(), key=lambda x: -sum(x[1].values())):
                total_count = sum(values.values())
                f.write(f"{total_count} {key}\n")

                mwe_items = {}
                non_mwe_items = {}

                for value, count in sorted(values.items(), key=lambda x: (-x[1], x[0])):
                    if "MWE[" in value:
                        mwe_items[value] = count
                    else:
                        non_mwe_items[value] = count

                f.write(f"{sum(non_mwe_items.values())} [NOT-MWE]\n")
                for value, count in non_mwe_items.items():
                    perc = (count / total_count) * 100
                    f.write(f"{count:>7}{perc:>7.2f}% {value}\n")

                f.write(f"{sum(mwe_items.values())} [MWE]\n")
                for value, count in mwe_items.items():
                    perc = (count / total_count) * 100
                    f.write(f"{count:>7}{perc:>7.2f}% {value}\n")
                f.write("\n")

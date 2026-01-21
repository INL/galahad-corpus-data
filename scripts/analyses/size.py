import json
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional, TextIO, Tuple

from data import TsvCorpus, TsvSplit, TsvSplits


class CorpusSize:
    def __init__(self, out: Path, corpus: TsvCorpus, metadata: Optional[Path] = None):
        with out.open("w") as f:
            self.subcorpus_size(f, corpus.splits)
            if metadata:
                self.century_size(f, corpus, metadata)
            self.subcorpus_size(f, corpus)
            self.subcorpus_size(f, corpus.train)
            self.subcorpus_size(f, corpus.test)
            self.subcorpus_size(f, corpus.dev)
            # subcorpora sorted by token count
            for sub in sorted(corpus.dirs, key=lambda d: -len(list(d.words))):
                self.subcorpus_size(f, sub, name=lambda d: d.split)

    def subcorpus_size(
        self,
        f: TextIO,
        corpus: TsvCorpus | TsvSplit | TsvSplits,
        name: Callable = lambda d: d.name,
    ):
        # header
        total = self.total_header(f, corpus)
        # subcorpora sorted by token count
        for sub in sorted(corpus, key=lambda t: -len(list(t.words))):
            w = len(list(sub.words))
            d = len(list(sub.docs))
            f.write(f"{name(sub):<25}{w:>10,}{w / total:>10.2%}{d:>10}\n")
        f.write("\n")

    def total_header(self, f: TextIO, corpus: TsvCorpus):
        total = len(list(corpus.words))
        d = len(list(corpus.docs))
        f.write(f"{corpus.name:<25}{total:>10,}{1:>10.2%}{d:>10}\n")
        return total

    def get_datasets_per_century(self, metadata: Path) -> dict[str, list[str]]:
        datasets_per_century = defaultdict(list)
        for dataset in json.loads(metadata.read_text()):
            start, end = dataset["period"].values()
            datasets_per_century[f"{start}-{end}"].append(dataset["name"])
        return datasets_per_century

    def century_size(
        self,
        f: TextIO,
        corpus: TsvCorpus,
        metadata: Path,
    ):
        self.total_header(f, corpus)
        datasets_per_century = self.get_datasets_per_century(metadata)

        total = len(list(corpus.words))
        century_totals: dict[str, Tuple[int, int]] = {}
        for century, dirs in sorted(datasets_per_century.items()):
            w = 0
            d = 0
            for dir in corpus.dirs:
                if dir.name in dirs:
                    w += len(list(dir.words))
                    d += len(list(dir.docs))
            century_totals[century] = (w, d)
            f.write(f"{century:<25}{w:>10,}{w / total:>10.2%}{d:>10}\n")
        f.write("\n")

        # same once more, but the century itself is the total, and it is broken down into subcorpora (dirs)
        for century, dirs in sorted(datasets_per_century.items()):
            total, d = century_totals[century]
            f.write(f"{century:<25}{total:>10,}{1:>10.2%}{d:>10}\n")
            for sub in sorted(corpus.dirs, key=lambda d: -len(list(d.words))):
                if sub.name in dirs:
                    w = len(list(sub.words))
                    d = len(list(sub.docs))
                    f.write(f"{sub.name:<25}{w:>10,}{w / total:>10.2%}{d:>10}\n")
            f.write("\n")

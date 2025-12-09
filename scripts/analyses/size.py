from pathlib import Path
from typing import Callable, Iterator, TextIO

from data import TsvCorpus, TsvDir, TsvWord


class CorpusSize:
    def __init__(self, out: Path, corpus: TsvCorpus):
        self.corpus = corpus
        with out.open("w") as f:
            train = len(list(corpus.train_words))
            dev = len(list(corpus.dev_words))
            test = len(list(corpus.test_words))
            total = len(list(corpus.words))
            f.write(
                f"{'total':<25}{total:>10,}{1:>10.2%}\n"
                f"{'train':<25}{train:>10,}{train / total:>10.2%}\n"
                f"{'test':<25}{test:>10,}{test / total:>10.2%}\n"
                f"{'dev':<25}{dev:>10,}{dev / total:>10.2%}\n"
            )
            f.write("\n")

            self.size_per_split(f, "total", total, lambda d: d.words)
            self.size_per_split(f, "train", train, lambda d: d.train.words)
            self.size_per_split(f, "test", test, lambda d: d.test.words)
            self.size_per_split(f, "dev", dev, lambda d: d.dev.words)

            for dir in corpus.dirs:
                self.size_per_project(f, dir)

    def size_per_split(
        self,
        f: TextIO,
        name: str,
        total: int,
        words: Callable[[TsvDir], Iterator[TsvWord]],
    ):
        f.write(f"{name:<25}{total:>10,}{1:>10.2%}\n")
        dirs = sorted(self.corpus.dirs, key=lambda d: -len(list(words(d))))
        for dir in dirs:
            size = len(list(words(dir)))
            f.write(f"{dir.name:<25}{size:>10,}{size / total:>10.2%}\n")
        f.write("\n")

    def size_per_project(self, f: TextIO, dir: TsvDir):
        total = len(list(dir.words))
        name = f"{dir.name}"
        f.write(f"{name:<25}{total:>10,}{1:>10.2%}\n")

        for split in dir.splits:
            size = len(list(split.words))
            f.write(f"{split.split:<25}{size:>10,}{size / total:>10.2%}\n")
        f.write("\n")

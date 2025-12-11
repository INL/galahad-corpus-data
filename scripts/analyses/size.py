from pathlib import Path
from typing import Callable, Iterable, TextIO

from data import TsvCorpus, TsvDir, TsvDocument, TsvWord


class CorpusSize:
    def __init__(self, out: Path, corpus: TsvCorpus):
        self.corpus = corpus
        with out.open("w") as f:
            train = len(list(corpus.train_words))
            dev = len(
                list(corpus.dev_words)
            )  # len(w for f in corpus.dev for w in f.words)
            test = len(list(corpus.test_words))
            total = len(list(corpus.words))
            total_docs = len(list(corpus.docs))
            train_docs = len(list([d for f in corpus.train for d in f.docs]))
            dev_docs = len(list([d for f in corpus.dev for d in f.docs]))
            test_docs = len(list([d for f in corpus.test for d in f.docs]))
            f.write(f"{'name':<25}{'tokens':>10}{'tokens%':>10}{'docs':>10}\n")
            f.write(
                f"{'total':<25}{total:>10,}{1:>10.2%}{total_docs:>10}\n"
                f"{'train':<25}{train:>10,}{train / total:>10.2%}{train_docs:>10}\n"
                f"{'test':<25}{test:>10,}{test / total:>10.2%}{test_docs:>10}\n"
                f"{'dev':<25}{dev:>10,}{dev / total:>10.2%}{dev_docs:>10}\n"
            )
            f.write("\n")

            # simplify to just corpus.test, corpus.dev etc.
            # total_words = len(w for f in corpus.test for w in f.words)
            # for f in corpus.test:
            #     project_words = len(list(f.words))
            self.size_per_split(
                f, "total", total, total_docs, lambda d: d.words, lambda d: d.docs
            )
            self.size_per_split(
                f,
                "train",
                train,
                train_docs,
                lambda d: d.train.words,
                lambda d: d.train.docs,
            )
            self.size_per_split(
                f,
                "test",
                test,
                test_docs,
                lambda d: d.test.words,
                lambda d: d.test.docs,
            )
            self.size_per_split(
                f, "dev", dev, dev_docs, lambda d: d.dev.words, lambda d: d.dev.docs
            )

            for dir in corpus.dirs:
                self.size_per_project(f, dir)

    def size_per_split(
        self,
        f: TextIO,
        name: str,
        total: int,
        total_docs: int,
        words: Callable[[TsvDir], Iterable[TsvWord]],
        docs: Callable[[TsvDir], Iterable[TsvDocument]],
    ):
        f.write(f"{name:<25}{total:>10,}{1:>10.2%}{total_docs:>10}\n")
        dirs = sorted(self.corpus.dirs, key=lambda d: -len(list(words(d))))
        for dir in dirs:
            size = len(list(words(dir)))
            docs_count = len(list(docs(dir)))
            f.write(f"{dir.name:<25}{size:>10,}{size / total:>10.2%}{docs_count:>10}\n")
        f.write("\n")

    def size_per_project(self, f: TextIO, dir: TsvDir):
        total = len(list(dir.words))
        name = f"{dir.name}"
        docs = len(list(dir.docs))
        f.write(f"{name:<25}{total:>10,}{1:>10.2%}{docs:>10}\n")

        for split in dir.splits:
            size = len(list(split.words))
            docs = len(list(split.docs))
            f.write(f"{split.split:<25}{size:>10,}{size / total:>10.2%}{docs:>10}\n")
        f.write("\n")

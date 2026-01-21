from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from os import name
from pathlib import Path
from typing import Iterator


class Split(StrEnum):
    TRAIN = "train"
    DEV = "dev"
    TEST = "test"


@dataclass
class TsvWord:
    token: str
    pos: str
    lemma: str
    group: str
    mwe: list["TsvWord"] = field(default_factory=list)

    @staticmethod
    def load(text: str) -> "TsvWord":
        cols = text.split("\t")
        return TsvWord(cols[0], cols[1], cols[2], cols[3])

    def __str__(self) -> str:
        return f"{self.token}\t{self.pos}\t{self.lemma}\t{self.group}"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class TsvSentence:
    words: list[TsvWord]

    @staticmethod
    def load(text: str) -> "TsvSentence":
        rows = text.split("\n")
        return TsvSentence([TsvWord.load(r) for r in rows if r.strip()])

    def __str__(self) -> str:
        return f"          Sentence ({len(self.words)} words)"  # \n{'\n'.join([str(r) for r in self.words])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.words)


@dataclass
class TsvParagraph:
    sents: list[TsvSentence]

    @property
    def words(self) -> Iterator[TsvWord]:
        for s in self.sents:
            for w in s.words:
                yield w

    @staticmethod
    def load(text: str) -> "TsvParagraph":
        # sentences are split by one empty row
        sents = text.split("\n\n")
        return TsvParagraph([TsvSentence.load(s) for s in sents if s.strip()])

    def __str__(self) -> str:
        return f"        Paragraph ({len(self.sents)} sents)\n{'\n'.join([str(s) for s in self.sents])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.sents)


@dataclass
class TsvDocument:
    pars: list[TsvParagraph]

    @property
    def sents(self) -> Iterator[TsvSentence]:
        for p in self.pars:
            for s in p.sents:
                yield s

    @property
    def words(self) -> Iterator[TsvWord]:
        for p in self.pars:
            for w in p.words:
                yield w

    @staticmethod
    def load(text: str) -> "TsvDocument":
        # paragraphs are split by two empty rows
        pars = text.split("\n\n\n")
        doc = TsvDocument([TsvParagraph.load(p) for p in pars if p.strip()])
        TsvDocument._link_mwes(doc)
        return doc

    @staticmethod
    def _link_mwes(doc: "TsvDocument") -> None:
        # collect groups
        group_map: dict[str, list[TsvWord]] = defaultdict(list)
        for w in doc.words:
            if w.group:
                group_map[w.group].append(w)
        # link MWEs
        for group in group_map.values():
            for w in group:
                w.mwe = [mw for mw in group]

    def __str__(self) -> str:
        return f"      Document ({len(self.pars)} pars)\n{'\n'.join([str(p) for p in self.pars])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.pars)


@dataclass
class TsvFile:
    filename: str
    docs: list[TsvDocument]

    @property
    def name(self) -> str:
        return self.filename.split(".")[0]

    @property
    def split(self) -> Split:
        return Split(self.filename.split(".")[1])

    @property
    def pars(self) -> Iterator[TsvParagraph]:
        for d in self.docs:
            for p in d.pars:
                yield p

    @property
    def sents(self) -> Iterator[TsvSentence]:
        for d in self.docs:
            for s in d.sents:
                yield s

    @property
    def words(self) -> Iterator[TsvWord]:
        for d in self.docs:
            for w in d.words:
                yield w

    @staticmethod
    def load(f: Path) -> "TsvFile":
        rows = f.read_text()
        # docs are split by three empty rows
        docs = rows.split("\n\n\n\n") if rows else []
        return TsvFile(f.name, [TsvDocument.load(d) for d in docs if d.strip()])

    def __str__(self) -> str:
        return f"    {self.filename} ({len(self.docs)} docs)\n{'\n'.join([str(d) for d in self.docs])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.docs)


@dataclass
class TsvDir:
    name: str
    train: TsvFile
    test: TsvFile
    dev: TsvFile
    split: str = "total"

    @property
    def splits(self) -> list[TsvFile]:
        return [self.train, self.test, self.dev]

    @property
    def docs(self) -> Iterator[TsvDocument]:
        for split in self.splits:
            for d in split.docs:
                yield d

    @property
    def pars(self) -> Iterator[TsvParagraph]:
        for split in self.splits:
            for p in split.pars:
                yield p

    @property
    def sents(self) -> Iterator[TsvSentence]:
        for split in self.splits:
            for sent in split.sents:
                yield sent

    @property
    def words(self) -> Iterator[TsvWord]:
        for split in self.splits:
            for w in split.words:
                yield w

    @staticmethod
    def load(dir: Path) -> "TsvDir":
        train = TsvFile.load(dir / f"{dir.name}.train.tsv")
        test = TsvFile.load(dir / f"{dir.name}.test.tsv")
        dev = TsvFile.load(dir / f"{dir.name}.dev.tsv")
        return TsvDir(dir.name, train, test, dev)

    def __str__(self) -> str:
        return f"  {self.name}\n{'\n'.join([str(s) for s in self.splits])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.splits)


@dataclass
class TsvSplit:
    name: str
    files: list[TsvFile]

    @property
    def docs(self) -> Iterator[TsvDocument]:
        for f in self.files:
            for d in f.docs:
                yield d

    @property
    def words(self) -> Iterator[TsvWord]:
        for f in self.files:
            for w in f.words:
                yield w

    def __iter__(self):
        return iter(self.files)


@dataclass
class TsvSplits:
    train: TsvSplit
    dev: TsvSplit
    test: TsvSplit
    name: str = "total"

    @property
    def docs(self) -> Iterator[TsvDocument]:
        for s in self:
            for d in s.docs:
                yield d

    @property
    def words(self) -> Iterator[TsvWord]:
        for s in self:
            for w in s.words:
                yield w

    def __iter__(self):
        return iter([self.train, self.dev, self.test])


@dataclass
class TsvCorpus:
    dirs: list[TsvDir]
    name: str = "total"

    @property
    def docs(self) -> Iterator[TsvDocument]:
        for d in self.dirs:
            for doc in d.docs:
                yield doc

    @property
    def words(self) -> Iterator[TsvWord]:
        for d in self.dirs:
            for w in d.words:
                yield w

    @property
    def sents(self) -> Iterator[TsvSentence]:
        for d in self.dirs:
            for s in d.sents:
                yield s

    @property
    def train(self) -> TsvSplit:
        return TsvSplit("train", [d.train for d in self.dirs])

    @property
    def dev(self) -> TsvSplit:
        return TsvSplit("dev", [d.dev for d in self.dirs])

    @property
    def test(self) -> TsvSplit:
        return TsvSplit("test", [d.test for d in self.dirs])

    @property
    def splits(self) -> TsvSplits:
        return TsvSplits(self.train, self.dev, self.test)

    @staticmethod
    def load(dir: Path) -> "TsvCorpus":
        return TsvCorpus([TsvDir.load(f) for f in sorted(dir.iterdir()) if f.is_dir()])

    def __str__(self) -> str:
        return f"{self.name}\n{'\n'.join([str(d) for d in self.dirs])}"

    def __repr__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter(self.dirs)

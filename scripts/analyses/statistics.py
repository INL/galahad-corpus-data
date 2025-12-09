#! /usr/bin/env python3
"""
Print basic statistics about a dataset.
- Number of tokens (total, per split)
- Number of unique tokens (total, per split)
- Same for lemmata and POS tags (total, per split)
- histogram of token frequencies (total, per split) (same for lemmata and POS tags)
- histogram of sentence lengths
- histogram of token lengths
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path

from data import TsvCorpus
from histogram import Histogram
from size import CorpusSize
from token_matcher import TokenMatcher


def generate_stats(corpus: TsvCorpus, out: Path):
    CorpusSize(out / "size.txt", corpus)
    histograms(corpus, out)
    empty_words(corpus, out)

    TokenMatcher(out / "words_tagged_pc.txt", corpus).filter(
        lambda w: w.pos == "PC" and w.token.isalpha()
    )
    TokenMatcher(out / "pc_not_tagged_pc.txt", corpus).filter(
        lambda w: not w.token.isalpha() and w.pos != "PC"
    )


def histograms(corpus: TsvCorpus, out: Path):
    hist = out / "histogram"
    hist.mkdir(parents=True, exist_ok=True)
    Histogram(hist / "token.txt").write(w.token for w in corpus.words)
    Histogram(hist / "lemma.txt").write(w.lemma for w in corpus.words)
    Histogram(hist / "pos.txt").write(w.pos for w in corpus.words)
    Histogram(hist / "token_char.txt").write(c for w in corpus.words for c in w.token)
    Histogram(hist / "lemma_char.txt").write(c for w in corpus.words for c in w.lemma)
    Histogram(hist / "pos_char.txt").write(c for w in corpus.words for c in w.pos)
    Histogram(hist / "sentence_len.txt").write(str(len(s.words)) for s in corpus.sents)
    Histogram(hist / "token_len.txt").write(str(len(w.token)) for w in corpus.words)


def empty_words(corpus: TsvCorpus, out: Path):
    empty = out / "empty"
    empty.mkdir(parents=True, exist_ok=True)
    TokenMatcher(empty / "lemma.txt", corpus).filter(lambda w: w.lemma.strip() == "")
    TokenMatcher(empty / "pos.txt", corpus).filter(lambda w: w.pos.strip() == "")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Print statistics about a dataset",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="TSV dir")
    parser.add_argument("output", type=Path, help="Stats dir")
    args = parser.parse_args()

    corpus = TsvCorpus.load(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    generate_stats(corpus, args.output)

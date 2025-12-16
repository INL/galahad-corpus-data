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
import re
import sys

from data import TsvCorpus
from histogram import Histogram
from token_grouper import TokenGrouper
from size import CorpusSize
from token_filter import TokenFilter

sys.path.append(str(Path(__file__).parent.parent))
from config.config import PUNCTUATION


def generate_stats(corpus: TsvCorpus, out: Path):
    CorpusSize(out / "size.txt", corpus)
    histograms(corpus, out)
    empty_words(corpus, out)
    punctuation(corpus, out)
    grouped_annotations(corpus, out)
    TokenFilter(out / "nou-p_no_capital.txt", corpus).filter(
        lambda w: w.pos == "NOU-P" and not any(c.isupper() for c in w.lemma)
    )

    # print all MWE tokens whose lemma is not identical
    with (out / "mwe_dif_lemma.txt").open("w") as f:
        for w in corpus.words:
            if any(mw.lemma != w.lemma for mw in w.mwe):
                f.write(f"{w.lemma} {w.group}\n")
                for mw in w.mwe:
                    f.write(f"\t{mw}\n")
                f.write("\n")

    # for each token, show how many times it occurs with each POS tag
    f_path = out / "token_pos.txt"
    token_pos_map = {}
    for w in corpus.words:
        pos_map = token_pos_map.get(w.token, {})
        key = f"{w.pos}-{w.lemma}"
        pos_map[key] = pos_map.get(key, 0) + 1
        token_pos_map[w.token] = pos_map
    with f_path.open("w") as f:
        for token, pos_map in sorted(
            token_pos_map.items(), key=lambda x: -sum(x[1].values())
        ):
            total_count = sum(pos_map.values())
            header_printed = False
            for pos, count in sorted(pos_map.items(), key=lambda x: -x[1]):
                if count < 0.05 * total_count:
                    if not header_printed:
                        header_printed = True
                        f.write(f"{token} (total: {total_count})\n")
                    f.write(f"    {pos}: {count}\n")


def histograms(corpus: TsvCorpus, out: Path):
    out = out / "histogram"
    out.mkdir(parents=True, exist_ok=True)
    Histogram(out / "pc.txt").write(w.token for w in corpus.words if w.pos == "PC")
    Histogram(out / "token.txt").write(w.token for w in corpus.words)
    Histogram(out / "lemma.txt").write(w.lemma for w in corpus.words if w.pos != "PC")
    Histogram(out / "pos.txt").write(w.pos for w in corpus.words)

    # ADP()+NOU-C()|PD()+NOU-C() => ADP+NOU-C|PD+NOU-C
    Histogram(out / "pos-main.txt").write(
        "|".join(
            "+".join(p.split("(")[0] for p in option_pos.split("+"))
            for option_pos in w.pos.split("|")
        )
        for w in corpus.words
    )
    Histogram(out / "group.txt").write(w.group for w in corpus.words)
    Histogram(out / "token_char.txt").write(c for w in corpus.words for c in w.token)
    Histogram(out / "lemma_char.txt").write(
        c for w in corpus.words for c in w.lemma if w.pos != "PC"
    )
    Histogram(out / "pos_char.txt").write(c for w in corpus.words for c in w.pos)
    Histogram(out / "sentence_len.txt").write(str(len(s.words)) for s in corpus.sents)
    Histogram(out / "token_len.txt").write(str(len(w.token)) for w in corpus.words)


def punctuation(corpus: TsvCorpus, out: Path):
    out = out / "pc"
    out.mkdir(parents=True, exist_ok=True)
    TokenFilter(out / "words_tagged_pc.txt", corpus).filter(
        lambda w: w.pos == "PC" and re.fullmatch(PUNCTUATION, w.token) is None
    )
    TokenFilter(out / "pc_not_tagged_pc.txt", corpus).filter(
        lambda w: re.fullmatch(PUNCTUATION, w.token) is not None and w.pos != "PC"
    )


def empty_words(corpus: TsvCorpus, out: Path):
    out = out / "empty"
    out.mkdir(parents=True, exist_ok=True)
    TokenFilter(out / "lemma.txt", corpus).filter(lambda w: w.lemma == "")
    Histogram(out / "lemma_hist.txt").write(
        w.token for w in corpus.words if w.lemma == ""
    )
    TokenFilter(out / "pos.txt", corpus).filter(lambda w: w.pos == "")
    Histogram(out / "pos_hist.txt").write(w.token for w in corpus.words if w.pos == "")


def grouped_annotations(corpus: TsvCorpus, out: Path):
    out = out / "grouped_annotations"
    out.mkdir(parents=True, exist_ok=True)
    # per token
    TokenGrouper(
        out / "lemma_per_token.txt",
        corpus,
        lambda w: w.token.lower(),
        lambda w: f"‘{w.lemma}’",
    )
    TokenGrouper(
        out / "pos_per_token.txt",
        corpus,
        lambda w: w.token.lower(),
        lambda w: w.pos,
    )
    # per lemma
    TokenGrouper(
        out / "token_per_lemma.txt",
        corpus,
        lambda w: f"‘{w.lemma}’",
        lambda w: w.token.lower(),
    )
    TokenGrouper(
        out / "pos_per_lemma.txt",
        corpus,
        lambda w: f"‘{w.lemma}’",
        lambda w: w.pos,
    )
    # per pos
    TokenGrouper(
        out / "token_per_pos.txt",
        corpus,
        lambda w: w.pos,
        lambda w: w.token.lower(),
    )
    TokenGrouper(
        out / "lemma_per_pos.txt",
        corpus,
        lambda w: w.pos,
        lambda w: f"‘{w.lemma}’",
    )
    # double per group
    TokenGrouper(
        out / "_tokenpos_per_lemma.txt",
        corpus,
        lambda w: f"‘{w.lemma}’",
        lambda w: f"{w.token.lower()} {w.pos}",
    )
    TokenGrouper(
        out / "_tokenlemma_per_pos.txt",
        corpus,
        lambda w: w.pos,
        lambda w: f"{w.token.lower()} ‘{w.lemma}’",
    )
    TokenGrouper(
        out / "_lemmapos_per_token.txt",
        corpus,
        lambda w: w.token.lower(),
        lambda w: f"‘{w.lemma}’ {w.pos}",
    )
    # per double group
    TokenGrouper(
        out / "token_per_lemmapos.txt",
        corpus,
        lambda w: f"‘{w.lemma}’ {w.pos}",
        lambda w: w.token.lower(),
    )
    TokenGrouper(
        out / "pos_per_tokenlemma.txt",
        corpus,
        lambda w: f"{w.token.lower()} ‘{w.lemma}’",
        lambda w: w.pos,
    )
    TokenGrouper(
        out / "lemma_per_tokenpos.txt",
        corpus,
        lambda w: f"{w.token.lower()} {w.pos}",
        lambda w: f"‘{w.lemma}’",
    )


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

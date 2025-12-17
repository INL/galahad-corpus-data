#! /usr/bin/env python3

"""
Analyse the input corpus, generate statistics, and note any suspicious patterns.
The following files are generated:
statistics/
    suspicious/
        mwe/
            mwe_dif_lemma.txt # MWEs where the lemmas of the components differ
            mwe_dif_pos.txt # MWEs where the POS of the components differ
        nou_p/
            nou-p_lemma_no_capital.txt # NOU-P tokens where the lemma does not contain a capital letter
        pc/
            words_tagged_pc.txt # tokens tagged as PC but not punctuation
            pc_not_tagged_pc.txt # punctuation tokens not tagged as PC
        roman_numerals/
            wrong_roman_numerals.txt # tokens where the lemma number does not match the roman numeral token
        empty/
            lemma.txt # tokens with empty lemma
            pos.txt # tokens with empty POS
    histogram/
        token.txt # histogram of tokens (excluding PC)
        lemma.txt # histogram of lemmas (excluding PC)
        pos.txt
        pos_main.txt # POS converted to main POS. NOU-C(num=sg) => NOU-C
        group.txt # histogram of group IDs
        pc.txt # histogram of tokens where POS = PC
        token_char.txt # histogram of characters in tokens
        lemma_char.txt
        token_len.txt # histogram of token lengths
        lemma_len.txt # histogram of lemma lengths
        sentence_len.txt # histogram of sentence lengths
    analyses/
        * # various grouped analyses, e.g., tok_to_lem.txt maps tokens to their lemmas
    size.txt # token size over various categories

"""

import re
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

from data import TsvCorpus, TsvWord
from histogram import Histogram
from size import CorpusSize
from token_filter import TokenFilter
from token_grouper import SuspiciousTokenGrouper, TokenGrouper
from util import pos_to_main_pos, roman_to_int

sys.path.append(str(Path(__file__).parent.parent))
from config.config import PUNCTUATION


def generate_stats(corpus: TsvCorpus, out: Path):
    generate_suspicious(corpus, out)
    grouped_annotations(corpus, out)
    CorpusSize(out / "size.txt", corpus)
    histograms(corpus, out)


def generate_suspicious(corpus: TsvCorpus, out: Path):
    out = out / "suspicious"
    out.mkdir(parents=True, exist_ok=True)
    suspicious_analyses(corpus, out)
    roman_numerals(corpus, out)
    mwe(corpus, out)
    nou_p(corpus, out)
    empty_words(corpus, out)
    punctuation(corpus, out)


def suspicious_analyses(corpus: TsvCorpus, out: Path):
    out = out / "analyses"
    out.mkdir(parents=True, exist_ok=True)
    SuspiciousTokenGrouper(
        out / "sus_lem_by_tokpos.txt",
        corpus,
        lambda w: f"{w.token.lower()} {w.pos}",
        lambda w: f"‘{w.lemma}’",
    ).report(out / "sus_lem_report_by_tokpos.txt", corpus)
    SuspiciousTokenGrouper(
        out / "sus_pos_by_toklem.txt",
        corpus,
        lambda w: f"{w.token.lower()} ‘{w.lemma}’",
        lambda w: w.pos,
    ).report(out / "sus_pos_report_by_toklem.txt", corpus)
    SuspiciousTokenGrouper(
        out / "sus_tok_by_lempos.txt",
        corpus,
        lambda w: f"‘{w.lemma}’ {w.pos}",
        lambda w: w.token.lower(),
    ).report(out / "sus_tok_report_by_lempos.txt", corpus)


def roman_numerals(corpus: TsvCorpus, out: Path):
    def convert_w(w: TsvWord) -> int:
        if w.group:
            concat = ".".join(m.token for m in w.mwe)
            return roman_to_int(concat)
        else:
            return roman_to_int(w.token)

    out = out / "roman_numerals"
    out.mkdir(parents=True, exist_ok=True)
    TokenFilter(out / "wrong_roman_numerals.txt", corpus).filter(
        lambda w: "representation=rom" in w.pos
        and str(convert_w(w)) != w.lemma
        and re.match(r"[0-9]", w.lemma) is not None,
        comment=lambda w: f"converted='{convert_w(w)}'",
    )


def mwe(corpus: TsvCorpus, out: Path):
    out = out / "mwe"
    out.mkdir(parents=True, exist_ok=True)
    TokenFilter(out / "mwe_dif_lemma.txt", corpus).filter(
        lambda w: any(m.lemma != w.lemma for m in w.mwe)
    )
    TokenFilter(out / "mwe_dif_pos.txt", corpus).filter(
        lambda w: any(m.pos != w.pos for m in w.mwe)
    )
    TokenFilter(out / "lonely_mwe.txt", corpus).filter(lambda w: len(w.mwe) == 1)


def nou_p(corpus: TsvCorpus, out: Path):
    out = out / "nou_p"
    out.mkdir(parents=True, exist_ok=True)
    TokenFilter(out / "nou-p_lemma_no_capital.txt", corpus).filter(
        lambda w: w.pos == "NOU-P" and not any(c.isupper() for c in w.lemma)
    )


def histograms(corp: TsvCorpus, out: Path):
    out = out / "histogram"
    out.mkdir(parents=True, exist_ok=True)
    Histogram(out / "token.txt").write(w.token for w in corp.words if w.pos != "PC")
    Histogram(out / "lemma.txt").write(w.lemma for w in corp.words if w.pos != "PC")
    Histogram(out / "pos.txt").write(w.pos for w in corp.words)
    Histogram(out / "pos_main.txt").write(pos_to_main_pos(w.pos) for w in corp.words)
    Histogram(out / "group.txt").write(w.group for w in corp.words)
    Histogram(out / "pc.txt").write(w.token for w in corp.words if w.pos == "PC")
    Histogram(out / "token_char.txt").write(
        c for w in corp.words for c in w.token if w.pos != "PC"
    )
    Histogram(out / "lemma_char.txt").write(
        c for w in corp.words for c in w.lemma if w.pos != "PC"
    )
    Histogram(out / "sentence_len.txt").write(str(len(s.words)) for s in corp.sents)
    Histogram(out / "token_len.txt").write(str(len(w.token)) for w in corp.words)
    Histogram(out / "lemma_len.txt").write(str(len(w.lemma)) for w in corp.words)


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
    TokenFilter(out / "pos.txt", corpus).filter(lambda w: w.pos == "")


def grouped_annotations(corp: TsvCorpus, out: Path):
    out = out / "analyses"
    out.mkdir(parents=True, exist_ok=True)
    TokenGrouper(
        out / "lem_by_tok.txt",
        corp,
        lambda w: w.token.lower(),
        lambda w: f"‘{w.lemma}’",
    )
    TokenGrouper(
        out / "pos_by_tok.txt", corp, lambda w: w.token.lower(), lambda w: w.pos
    )
    TokenGrouper(
        out / "lempos_by_tok.txt",
        corp,
        lambda w: w.token.lower(),
        lambda w: f"‘{w.lemma}’ {w.pos}",
    )
    TokenGrouper(
        out / "tok_by_lem.txt",
        corp,
        lambda w: f"‘{w.lemma}’",
        lambda w: w.token.lower(),
    )
    TokenGrouper(
        out / "pos_by_lem.txt", corp, lambda w: f"‘{w.lemma}’", lambda w: w.pos
    )
    TokenGrouper(
        out / "tokpos_by_lem.txt",
        corp,
        lambda w: f"‘{w.lemma}’",
        lambda w: f"{w.token.lower()} {w.pos}",
    )
    TokenGrouper(
        out / "tok_by_pos.txt", corp, lambda w: w.pos, lambda w: w.token.lower()
    )
    TokenGrouper(
        out / "lem_by_pos.txt", corp, lambda w: w.pos, lambda w: f"‘{w.lemma}’"
    )
    TokenGrouper(
        out / "toklem_by_pos.txt",
        corp,
        lambda w: w.pos,
        lambda w: f"{w.token.lower()} ‘{w.lemma}’",
    )
    TokenGrouper(
        out / "tok_by_lempos.txt",
        corp,
        lambda w: f"‘{w.lemma}’ {w.pos}",
        lambda w: w.token.lower(),
    )
    TokenGrouper(
        out / "pos_by_toklem.txt",
        corp,
        lambda w: f"{w.token.lower()} ‘{w.lemma}’",
        lambda w: w.pos,
    )
    TokenGrouper(
        out / "lem_by_tokpos.txt",
        corp,
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

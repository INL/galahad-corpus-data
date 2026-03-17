#!/usr/bin/env python3

"""
Given is a split.tsv and a directiory with original data files.
we split up split.tsv into groups of 5 lines. We then check for each group if there is a file with a full match
and print its filename.
"""

import re
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from itertools import groupby
from pathlib import Path


def file_to_text(path: Path) -> str:
    with Path(path).open(encoding="utf-8") as f:
        tokens = [line.split("\t")[0] for line in f]
        text = "".join(tokens)
        # remove everything that isn't [a-zA-Z]
        text = re.sub(r"[^a-zA-Z]", "", text.lower())
    return text


def get_data(split: Path, dir: Path) -> tuple[str, dict[str, str]]:
    split_txt = file_to_text(split)
    dir_txts: dict[str, str] = {}
    for f in dir.glob("*.tsv"):
        dir_txts[f.name] = file_to_text(f)
    return split_txt, dir_txts


def determine_split(split: Path, dir: Path, verbose: bool):
    split_txt, dir_txts = get_data(split, dir)
    matches: list[str] = []

    GROUP_SIZE = 30
    for i in range(0, len(split_txt), GROUP_SIZE):
        substr = split_txt[i : i + GROUP_SIZE]
        found = False
        for f, txt in dir_txts.items():
            if substr in txt:
                matches.append(f)
                found = True
                break
        if not found and verbose:
            matches.append("NO MATCH")

    groups = [(len(list(items)), f) for f, items in groupby(matches)]

    duplicates = [k for k in set(groups) if groups.count(k) > 1]
    if duplicates or verbose:
        for count, f in groups:
            print(f'"{Path(f).stem}",\t[{count}]')
        for d in duplicates:
            print(f"Duplicate: {d}")
    else:
        for _, f in groups:
            print(f'"{Path(f).stem}",')


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Determine original splits",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("split", type=Path, help="split.tsv")
    parser.add_argument("dir", type=Path, help="dir with unsplit data")
    parser.add_argument("--verbose", action="store_true", help="Whether to be verbose")
    args = parser.parse_args()
    if not args.split.is_file():
        raise ValueError(f"{args.split} is not a file")
    if not args.dir.is_dir():
        raise ValueError(f"{args.dir} is not a directory")

    determine_split(args.split, args.dir, args.verbose)

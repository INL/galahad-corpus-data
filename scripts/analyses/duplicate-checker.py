#!/usr/bin/env python3

"""
Given a directory with tsv files, we check for duplicate files based on their text content.
"""

import json
import operator
import re
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import edlib


def file_to_text(path: Path) -> str:
    with Path(path).open(encoding="utf-8") as f:
        tokens = [line.split("\t")[0] for line in f]
        text = "".join(tokens)
        # remove everything that isn't [a-zA-Z]
        text = re.sub(r"[^a-zA-Z]", "", text.lower())
    return text


def get_data(dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for f in dir.glob("*.tsv"):
        texts[f.stem] = file_to_text(f)
    return texts


def get_duplicates(
    texts: dict[str, str],
    window: int,
    distance: int,
    threads: int,
) -> dict[str, dict[str, list[str]]]:
    def process_file(f: str) -> dict[str, dict[str, list[str]]]:
        local_dups: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list),
        )
        txt = texts[f]
        for i in range(0, len(txt) - window, window):
            substr = txt[i : i + window]

            for other_f, other_txt in texts.items():
                if f != other_f:
                    if distance == 0:  # exact match
                        if substr in other_txt:
                            local_dups[f][other_f].append(substr)
                    else:  # edlib
                        dist = edlib.align(
                            substr,
                            other_txt,
                            mode="HW",
                            task="distance",
                            k=distance,
                        )["editDistance"]
                        if dist != -1:
                            local_dups[f][other_f].append(substr)
        return local_dups

    if threads > 1:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            results = executor.map(process_file, texts.keys())
        return {f: d for r in results for f, d in r.items()}
    dups: dict[str, dict[str, list[str]]] = {}
    for f in texts:
        local_dups = process_file(f)
        dups.update(local_dups)
    return dups


def sort_and_filter(
    duplicates: dict[str, dict[str, list[str]]],
    texts: dict[str, str],
    window: int,
    threshold: int,
) -> dict[str, dict[str, list[str]]]:
    filtered_duplicates: dict[str, dict[str, list[str]]] = {}
    for f, dups in duplicates.items():
        num_windows = len(texts[f]) // window
        # filter dups by threshold (%) and sort by count
        dups = {
            k: v for k, v in dups.items() if (len(v) / num_windows) * 100 >= threshold
        }
        dups = dict(sorted(dups.items(), key=lambda x: len(x[1]), reverse=True))
        if dups:
            filtered_duplicates[f] = dups
    return dict(
        sorted(
            filtered_duplicates.items(),
            key=lambda x: max(
                (len(v) / (len(texts[x[0]]) // window)) * 100 for v in x[1].values()
            ),
            reverse=True,
        ),
    )


def report_json(duplicates: dict[str, dict[str, list[str]]]):
    # print a list of lists. E.g.:
    # [ ["reinaert_a", "reinaert_b"], ["maerlant_a", "maerlant_b", "maerlant_c"] ]

    unique: list[set[str]] = []
    for f, dups in duplicates.items():
        files = [f, *dups.keys()]
        # check if any of these files are already in a unique set
        found = False
        for s in unique:
            if any(file in s for file in files):
                # add all files to this set
                s.update(file for file in files if file not in s)
                found = True
                break
        if not found:
            unique.append(set(files))
    # json needs lists
    output = [sorted(s) for s in unique]
    # sort the individual lists and the output list itself
    output.sort(key=operator.itemgetter(0))

    print(json.dumps(output, indent=4))


def report(
    duplicates: dict[str, dict[str, list[str]]],
    texts: dict[str, str],
    window: int,
):
    for f, dups in duplicates.items():
        num_windows = len(texts[f]) // window
        print(f"{f:<50}{num_windows:>10}{100:>10.1f}%")
        for other_f, substrs in dups.items():
            # what percent of the text is duplicate?
            percent = (len(substrs) / num_windows) * 100

            print(f"{other_f:<50}{len(substrs):>10}{percent:>10.1f}%")
        print()


def report_and_sort(
    duplicates: dict[str, dict[str, list[str]]],
    texts: dict[str, str],
    window: int,
    threshold: int,
    verbose: bool,
):
    for f, dups in sorted(
        duplicates.items(),
        key=lambda x: max(
            (len(v) / (len(texts[x[0]]) // window)) * 100 for v in x[1].values()
        ),
        reverse=True,
    ):  # sort by max percentage of duplicates found
        num_windows = len(texts[f]) // window
        # filter dups by threshold (%) and sort by count
        dups = {
            k: v for k, v in dups.items() if (len(v) / num_windows) * 100 >= threshold
        }
        dups = sorted(dups.items(), key=lambda x: len(x[1]), reverse=True)
        # if they survived threshold
        if dups:
            print(f"{f:<30}{num_windows:>10}{100:>10.1f}%")
            for other_f, substrs in dups:
                # what percent of the text is duplicate?
                percent = (len(substrs) / num_windows) * 100

                print(f"{other_f:<30}{len(substrs):>10}{percent:>10.1f}%")
                if verbose:
                    for s in substrs:
                        print(f"        {s}")
            print()


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Duplicate finder",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "dir",
        type=Path,
        help="Directory with tsv files to check for duplicates.",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=10,
        help="Threshold percentage of matching chunks to consider as duplicate.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Whether to be verbose.",
    )
    parser.add_argument(
        "--window",
        "-w",
        type=int,
        default=20,
        help="Size of text chunks to compare.",
    )
    parser.add_argument(
        "--distance",
        "-d",
        type=int,
        default=5,
        help="Maximum edit distance to consider a match.",
    )
    parser.add_argument(
        "--multithreads",
        "-m",
        type=int,
        default=2,
        help="Number of threads to use. If 1, no multithreading is used.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print json",
    )
    args = parser.parse_args()

    if not args.dir.is_dir():
        raise ValueError(f"{args.dir} is not a directory.")
    if args.threshold < 0:
        raise ValueError("Threshold must be non-negative.")
    if args.window <= 0:
        raise ValueError("Window size must be greater than 0.")
    if args.distance < 0:
        raise ValueError("Distance must be non-negative.")

    texts: dict[str, str] = get_data(args.dir)
    duplicates = get_duplicates(texts, args.window, args.distance, args.multithreads)
    filtered = sort_and_filter(duplicates, texts, args.window, args.threshold)
    if args.json:
        report_json(filtered)
    else:
        report(filtered, texts, args.window)

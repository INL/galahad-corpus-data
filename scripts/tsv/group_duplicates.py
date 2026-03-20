#!/usr/bin/env python3

"""
Given a splits.json file, check for each list of duplicates in json["duplicates"] whether
all these files are within the same split. If they are not, move all files to the same split.
For this, simply move them to the split of the first file in the list.
"""

import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path


def group_dupes_in_split(splits_file: Path):
    data = json.loads(splits_file.read_text(encoding="utf-8"))
    duplicates: list[list[str]] = data.get("duplicates", [])
    if not duplicates:
        print("No duplicates found in splits file.")
        return
    # load current splits
    for dups in duplicates:
        splits: set[str] = set()
        for f in dups:
            for split_name, files in data.items():
                if split_name != "duplicates" and f in files:
                    splits.add(split_name)
        if len(splits) > 1:
            target_split = list(splits)[0]
            print(
                f"Warning: Duplicates {dups} are in multiple splits {splits}. Moving all to {target_split}.",
            )
            for f in dups:
                # remove from other splits
                for split_name, files in data.items():
                    if split_name != "duplicates" and f in files:
                        files.remove(f)
                # add to target split
                if f not in data[target_split]:
                    data[target_split].append(f)
    # write back updated splits
    splits_file.write_text(json.dumps(data, indent=4), encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Group duplicate files into the same split based on splits.json",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "splits_file",
        type=Path,
        help="Path to the splits.json file",
    )

    args = parser.parse_args()
    group_dupes_in_split(args.splits_file)

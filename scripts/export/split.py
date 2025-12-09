#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import json
import random

split_types = ["train", "dev", "test"]
split_probs = [0.8, 0.1, 0.1]


def create_split(input: Path, output: Path):
    # create a subdir for this project
    project_name = input.name
    project_output = output / input.name
    project_output.mkdir(parents=True, exist_ok=True)

    # define split files
    train = project_output / f"{project_name}.train.tsv"
    dev = project_output / f"{project_name}.dev.tsv"
    test = project_output / f"{project_name}.test.tsv"

    partition_info: dict[str, list[str]] = {"train": [], "dev": [], "test": []}
    with (
        train.open("w", encoding="utf-8") as train_f,
        dev.open("w", encoding="utf-8") as dev_f,
        test.open("w", encoding="utf-8") as test_f,
    ):
        split_files = {"train": train_f, "dev": dev_f, "test": test_f}

        # if there are 3 or less files
        files = list(input.iterdir())
        if len(files) <= 3:
            print("\tUsing ordered split")
            # 1: train, 2: test(!), 3: dev
            ordered_splits = ["train", "test", "dev"][: len(files)]
            for f, s in zip(files, ordered_splits):
                partition_info[s].append(f.stem)
                split_files[s].write(f.read_text() + "\n\n\n")

        else:  # random
            print("\tUsing random split")
            for f in input.iterdir():
                # randomly split files into train/dev/test 80/10/10
                s = random.choices(split_types, weights=split_probs)[0]
                partition_info[s].append(f.stem)
                split_files[s].write(f.read_text() + "\n\n\n")

    # write partition info
    partition_file = project_output / f"{project_name}.splits.json"
    partition_file.write_text(json.dumps(partition_info, indent=4))


def reproduce_split(input: Path, output: Path):
    """
    Reproduce splits based on existing partition.json at output directory
    """
    # load partition info
    project_name = input.name
    project_output = output / input.name
    partition_file = project_output / f"{project_name}.splits.json"
    partition_info: dict[str, list[str]] = json.loads(partition_file.read_text())

    # define split files
    train = project_output / f"{project_name}.train.tsv"
    dev = project_output / f"{project_name}.dev.tsv"
    test = project_output / f"{project_name}.test.tsv"

    with (
        train.open("w", encoding="utf-8") as train_f,
        dev.open("w", encoding="utf-8") as dev_f,
        test.open("w", encoding="utf-8") as test_f,
    ):
        split_files = {"train": train_f, "dev": dev_f, "test": test_f}
        for split_type in split_types:
            out_file = split_files[split_type]
            for stem in partition_info[split_type]:
                f = input / f"{stem}.tsv"
                tokens = f.read_text()
                out_file.write(tokens)
                out_file.write("\n\n\n")


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot tsv splitter",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", type=Path, help="Directory containing project subdirectories"
    )
    parser.add_argument("outdir", type=Path, help="Output directory for split files")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    for project_dir in args.input.iterdir():
        print(f"Processing project: {project_dir.name}")
        num_of_files = len(list(project_dir.iterdir()))
        print(f"\tNumber of files: {num_of_files}")

        partition_file = (
            args.outdir / project_dir.name / f"{project_dir.name}.splits.json"
        )
        if partition_file.exists():
            print("\tReproducing existing split")
            # do check wether the number of files match
            part_j = json.loads(partition_file.read_text())
            total_j = len(part_j["train"]) + len(part_j["dev"]) + len(part_j["test"])
            if total_j != num_of_files:
                print("\tNumber of files do not match, creating new split")
                print(f"\tJSON: {total_j} files; Folder: {num_of_files} files")
                create_split(project_dir, args.outdir)
            else:
                reproduce_split(project_dir, args.outdir)
        else:
            print("\tCreating new split")
            create_split(project_dir, args.outdir)

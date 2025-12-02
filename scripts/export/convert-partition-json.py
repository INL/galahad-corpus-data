#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import json
import random


def convert_partition_json(input: Path):
    json_file = project_dir / f"{project_dir.name}.partitionInformation.json"
    j = json.loads(json_file.read_text())
    new_j = {"train": [], "dev": [], "test": []}
    for split_type in ["train", "dev", "test"]:
        for item in j["partitions"][split_type]["documents"]:
            if "sentenceIds" in item:
                # this cannot be converted
                print(f"Skipping {project_dir.name} due to sentenceIds")
                return
            f = item[
                "sourceFileName"
            ]  # this is the full file name, new format uses stem
            stem = Path(f).stem.removesuffix(".tei")
            new_j[split_type].append(stem)
    new_json_file = project_dir / f"{project_dir.name}.partitions.json"
    new_json_file.write_text(json.dumps(new_j, indent=4))


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot partition json updater",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Directory containing project subdirectories with old partition jsons",
    )
    args = parser.parse_args()

    for project_dir in args.input.iterdir():
        print(f"Processing project: {project_dir.name}")
        convert_partition_json(project_dir)

#!/usr/bin/env python3

import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Determine original splits",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("split", type=Path, help="split.json")
    args = parser.parse_args()
    if not args.split.is_file():
        raise ValueError(f"{args.split} is not a file")

    p: dict[str, list[str]] = json.loads(args.split.read_text())["partitions"]
    dev = p["train"]["documents"]
    dev_f = [item["sourceFileName"] for item in dev]
    for f in sorted(dev_f, reverse=True):
        print(f'"{Path(f).stem}",')

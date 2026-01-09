#! /usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import os

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot TSV column fixer",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("dir", type=Path, help="Directory containing .tsv files")
    parser.add_argument("-r", action="store_true", help="Recursive")
    args = parser.parse_args()

    files = list(args.dir.rglob("*.tsv") if args.r else args.dir.glob("*.tsv"))
    for file in files:
        os.system(
            f"awk -F'\\t' -v OFS='\\t' '{{print $2, $4, $3, $NF}}' {file} | tail -n +2 > {file}.fixed"
        )
        os.replace(f"{file}.fixed", file)
        # dos2unix conversion
        os.system(f"dos2unix {file}")
        # awk will create "empty" rows (with only tabs): replace them with empty lines (dont delete!)
        os.system(f"sed -i 's/^[\t]*$//' {file}")

    print(f"Fixed {len(files)} files.")

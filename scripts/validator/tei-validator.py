#!/usr/bin/env python3

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

from lxml import etree


def validate(f: Path, validator, verbose: bool):
    """Print if file is invalid. Print specific validations errors when vebose"""
    # try to parse the input xml
    # if it fails, no need to check DTD: it's invalid
    try:
        tree = etree.parse(f)
        valid = validator.validate(tree)
    except Exception as e:
        print(f"{f.name} is unparsable")
        if verbose:
            print(f"\t{e}")
        return False

    if not valid:
        if verbose:
            # get unique error messages in set
            messages = set(e.message for e in validator.error_log)
            # get the lowest line number for each message
            messages = set(
                f"Line {min(e.line for e in validator.error_log if e.message == msg)}: {msg}"
                for msg in messages
            )

            print(f"{f.name} contains {len(messages)} error(s):")
            for msg in sorted(messages):
                print(f"\t{msg}")
        else:
            print(f"{f.name} is invalid")
    return valid


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot TEI DTD validator",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-r", action="store_true", help="Recursive")
    parser.add_argument("-v", action="store_true", help="verbose")
    parser.add_argument("dtd", type=Path, help="dtd file")
    parser.add_argument("input", type=Path, help="xml file or dir")
    args = parser.parse_args()

    # load the DTD once for all files
    validator = etree.RelaxNG(file=args.dtd)
    print("Loaded DTD")

    if args.input.is_file():
        validate(args.input, validator, args.v)
    else:
        # count valid files
        n_valid = 0
        # get all files in dir, and/or subdirs if recursive
        files = list(args.input.rglob("*.xml") if args.r else args.input.glob("*.xml"))
        for f in files:
            n_valid += validate(f, validator, args.v)
        print(f"Total: {n_valid}/{len(files)} valid")

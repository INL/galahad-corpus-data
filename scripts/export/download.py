#! /usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from io import BytesIO
import json
from operator import ne
from pathlib import Path
import urllib.request
from zipfile import ZipFile, Path as ZipPath

from timer import Timer


def download_single(outdir: Path, host: str, d: dict[str, str]):
    name = d["name"]
    id = d["lancelotID"]
    url = f"{host}/CobaltServe/webservice/api/export/?only_validated=false&project_name={id}"
    print(f"Processing {name} ({id})")
    dataset_dir = outdir / Path(name)
    dataset_dir.mkdir(exist_ok=True, parents=True)

    with Timer("Total"):
        with Timer("Exporting"):
            with urllib.request.urlopen(url) as res:
                bytes = res.read()
        with Timer("Extracting"):
            with ZipFile(BytesIO(bytes)) as zip:
                for path in ZipPath(zip, at="LancelotExport/").iterdir():
                    file = path.stem + path.suffix.lower()  # lower .XML
                    (dataset_dir / file).write_bytes(path.read_bytes())


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot Downloader",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://localhost:8080",
        help="Host URL of the Lancelot server",
    )
    parser.add_argument(
        "--datasets",
        type=Path,
        default=Path("datasets.json"),
        help="Path to the JSON file containing datasets IDs and names",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name of a single dataset to download",
    )
    parser.add_argument(
        "outdir", type=Path, help="Output directory for downloaded datasets"
    )
    args = parser.parse_args()

    try:
        datasets = json.load(open(args.datasets))
        if args.name:
            d = next((d for d in datasets if d["name"] == args.name), None)
            if d is None:
                print(f"Dataset with name {args.name} not found in {args.datasets}.")
            else:
                download_single(args.outdir, args.host, d)
        else:
            for d in datasets:
                download_single(args.outdir, args.host, d)
    except FileNotFoundError:
        print(f"{args.datasets} not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing datasets file: {e}")

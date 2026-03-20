"""Download projects from Lancelot."""

import json
import urllib.request
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from io import BytesIO
from pathlib import Path
from zipfile import Path as ZipPath
from zipfile import ZipFile

from scripts.util.timer import Timer


def download_single(outdir: Path, host: str, d: dict[str, str]) -> None:
    """Download a single dataset."""
    name = d["name"]
    project_id = d["lancelotID"]
    url = f"{host}/CobaltServe/webservice/api/export/?only_validated=false&project_name={project_id}"
    print(f"Processing {name} ({project_id})")
    dataset_dir = outdir / Path(name)
    dataset_dir.mkdir(exist_ok=True, parents=True)

    with Timer("Total"):
        with Timer("Exporting"), urllib.request.urlopen(url) as res:
            data = res.read()
        with Timer("Extracting"), ZipFile(BytesIO(data)) as zip_file:
            for path in ZipPath(zip_file, at="LancelotExport/").iterdir():
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
        "outdir",
        type=Path,
        help="Output directory for downloaded datasets",
    )
    args = parser.parse_args()

    try:
        with Path(args.datasets).open(encoding="utf-8") as f:
            datasets = json.load(f)
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

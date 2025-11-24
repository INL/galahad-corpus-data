#! /usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from contextlib import ContextDecorator
from io import BytesIO
import json
from pathlib import Path
from time import perf_counter
import urllib.request
from zipfile import ZipFile, Path as ZipPath


class Timer(ContextDecorator):
    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *_):
        pass

    @property
    def elapsed(self) -> float:
        return perf_counter() - self.start


def download(outdir: Path, host: str, projects: dict[str, str]):
    for id, name in projects.items():
        url = f"{host}/CobaltServe/webservice/api/export/?only_validated=false&project_name={id}"
        print(f"Exporting {name} ({id})")
        project_dir = outdir / Path(name)
        project_dir.mkdir(exist_ok=True, parents=True)

        with Timer() as t:
            with urllib.request.urlopen(url) as res:
                print(f"\tDownloaded in {t.elapsed:.2f}s")
                with ZipFile(BytesIO(res.read())) as zip:
                    with Timer() as t2:
                        for path in ZipPath(zip, at="LancelotExport/").iterdir():
                            (project_dir / path.name).write_bytes(path.read_bytes())
                    print(f"\tExtracted in {t2.elapsed:.2f}s")
            print(f"\tTotal: {t.elapsed:.2f}s\n")


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
        "--projects",
        type=Path,
        default=Path("projects.json"),
        help="Path to the JSON file containing project IDs and names",
    )
    parser.add_argument(
        "outdir", type=Path, help="Output directory for downloaded projects"
    )
    args = parser.parse_args()

    try:
        projects = json.load(open(args.projects))
        download(args.outdir, args.host, projects)
    except FileNotFoundError:
        print(f"{args.projects} not found.")
    except json.JSONDecodeError as e:
        print(f"Error parsing projects file: {e}")

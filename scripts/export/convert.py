#!/usr/bin/env python3

import json
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import Path as ZipPath
from zipfile import ZipFile

from timer import Timer
from ziputil import MultiPartFile, zipdir


def create(name: str, api: str) -> str:
    data = json.dumps(
        {"name": name, "owner": "user", "collaborators": [], "viewers": []},
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = Request(f"{api}/corpora", data=data, headers=headers)
    with urlopen(req) as res:
        return json.load(res)


def delete(api: str, uuid: str):
    req = Request(f"{api}/corpora/{uuid}", method="DELETE")
    urlopen(req)


def upload(api: str, uuid: str, zip: BytesIO):
    mp = MultiPartFile(zip.read(), name="file")
    req = Request(f"{api}/corpora/{uuid}/documents", data=bytes(mp), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={mp.boundary}")
    urlopen(req)


def export(api: str, uuid: str) -> BytesIO:
    url = f"{api}/corpora/{uuid}/jobs/sourceLayer/export/convert?format=tsv"
    with urlopen(url) as res:
        return BytesIO(res.read())


def unzip(bytes: BytesIO, out: Path):
    with ZipFile(bytes, "r") as zip:
        for path in ZipPath(zip).iterdir():
            if path.is_file():  # ignore metadata/ dir
                zip.extract(path.name, out)


def convert(dir: Path, api: str, out: Path):
    print(f"Processing {dir.name}")
    uuid = create(dir.name, api)
    with Timer("Zipping"):
        zip = zipdir(dir)

    with Timer("Uploading"):
        upload(api, uuid, zip)

    with Timer("Exporting"):
        zip = export(api, uuid)

    with Timer("Extracting"):
        unzip(zip, out / dir.name)

    with Timer("Cleaning"):
        delete(api, uuid)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot-Galahad TEI to TSV converter",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        type=str,
        default="http://localhost:8010",
        help="Galahad API base URL",
    )
    parser.add_argument("-r", action="store_true", help="Recursive")
    parser.add_argument(
        "input",
        type=Path,
        help="Directory containing project or project subdirectories",
    )
    parser.add_argument("outdir", type=Path, help="Output directory for TSV data")
    args = parser.parse_args()

    args.outdir.mkdir(exist_ok=True)

    with Timer("Total"):
        if args.r:
            for project_dir in args.input.iterdir():
                if project_dir.is_dir():
                    convert(project_dir, args.api, args.outdir)
        else:
            convert(args.input, args.api, args.outdir)

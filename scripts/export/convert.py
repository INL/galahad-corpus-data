#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from io import BytesIO
import json
from pathlib import Path
from urllib.request import urlopen, Request
from uuid import uuid4
from zipfile import ZipFile, Path as ZipPath

from timer import Timer


class MultiPartFile:
    def __init__(self, file: bytes):
        self.boundary = uuid4().hex
        self.file = file

    def __bytes__(self):
        header = f"""--{self.boundary}\r\n
        Content-Disposition: form-data; name="file"; filename=corpus.zip\r\n
        Content-Type: application/octet-stream\r\n\r\n"""
        footer = f"\r\n--{self.boundary}--\r\n"
        return header.encode() + self.file + footer.encode()


def create(name: str, api: str) -> str:
    data = json.dumps(
        {"name": name, "owner": "user", "collaborators": [], "viewers": []}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = Request(f"{api}/corpora", data=data, headers=headers)
    with urlopen(req) as res:
        return json.load(res)


def delete(api: str, uuid: str):
    req = Request(f"{api}/corpora/{uuid}", method="DELETE")
    urlopen(req)


def zipdir(dir: Path) -> BytesIO:
    buf = BytesIO()
    with ZipFile(buf, "w") as z:
        for f in dir.iterdir():
            if f.is_file():
                z.write(f, arcname=f.name)
    buf.seek(0)  # reset buffer pointer
    return buf


def upload(api: str, uuid: str, zip: BytesIO):
    mp = MultiPartFile(zip.read())
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
    parser.add_argument(
        "input", type=Path, help="Directory containing project subdirectories"
    )
    parser.add_argument("outdir", type=Path, help="Output directory for TSV data")
    args = parser.parse_args()

    args.outdir.mkdir(exist_ok=True)

    for project_dir in args.input.iterdir():
        if project_dir.is_dir():
            with Timer("Total"):
                convert(project_dir, args.api, args.outdir)

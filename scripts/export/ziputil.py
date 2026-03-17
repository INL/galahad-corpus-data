from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


class MultiPartFile:
    def __init__(
        self,
        file: bytes,
        name: str = "data",
        content_type: str = "application/zip",
    ):
        self.boundary = uuid4().hex
        self.file = file
        self.content_type = content_type
        self.name = name

    def __bytes__(self):
        header = f"""--{self.boundary}\r\n
        Content-Disposition: form-data; name="{self.name}"; filename="corpus.zip"\r\n
        Content-Type: {self.content_type}\r\n\r\n"""
        footer = f"\r\n--{self.boundary}--\r\n"
        return header.encode() + self.file + footer.encode()


def zipdir(dir: Path, recursive: bool = False) -> BytesIO:
    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED) as z:
        files = dir.rglob("*") if recursive else dir.glob("*")
        for f in files:
            if f.is_file():
                z.write(f, arcname=f.name)
    buf.seek(0)  # reset buffer pointer
    return buf

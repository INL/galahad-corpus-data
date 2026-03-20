"""Utility for sending zip files over HTTP."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


class MultiPartFile:
    """Helper class for sending multipart files."""

    def __init__(
        self,
        file: bytes,
        name: str = "data",
        content_type: str = "application/zip",
    ) -> None:
        """Create a multipart file of type @content_type and form-data name @name."""
        self.boundary = uuid4().hex
        self.file = file
        self.content_type = content_type
        self.name = name

    def __bytes__(self) -> bytes:
        """Return multipart files at HTTP bytes body."""
        header = f"""--{self.boundary}\r\n
        Content-Disposition: form-data; name="{self.name}"; filename="corpus.zip"\r\n
        Content-Type: {self.content_type}\r\n\r\n"""
        footer = f"\r\n--{self.boundary}--\r\n"
        return header.encode() + self.file + footer.encode()


def zip_folder(folder: Path, *, recursive: bool = False) -> BytesIO:
    """Return zipped folder as bytes."""
    buf = BytesIO()
    with ZipFile(buf, "w", compression=ZIP_DEFLATED) as z:
        files = folder.rglob("*") if recursive else folder.glob("*")
        for f in files:
            if f.is_file():
                z.write(f, arcname=f.name)
    buf.seek(0)  # reset buffer pointer
    return buf

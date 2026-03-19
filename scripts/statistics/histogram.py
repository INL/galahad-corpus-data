"""Histogram generator backed by GNU `sort` & `uniq`."""

import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Histogram:
    """Annotations histogram written to a file."""

    out: Path

    def write(self, annotations: Iterable[str]) -> None:
        """Count and rank annotations by frequency and write to out."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as f:
            f.write("\n".join(annotations))
            f.flush()
            cmd = f"sort {f.name} | uniq -c | sort -nr"
            stream = os.popen(cmd)
            self.out.write_text(stream.read())

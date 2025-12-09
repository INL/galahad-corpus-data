from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import os
import tempfile


@dataclass
class Histogram:
    out: Path

    def write(self, annotations: Iterator[str]):
        with tempfile.NamedTemporaryFile("w") as f:
            f.write("\n".join(annotations))
            cmd = f"sort {f.name} | uniq -c | sort -nr"
            stream = os.popen(cmd)
            self.out.write_text(stream.read())

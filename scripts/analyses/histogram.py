from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import os
import tempfile


@dataclass
class Histogram:
    out: Path

    def write(self, annotations: Iterable[str]):
        with tempfile.NamedTemporaryFile("w") as f:
            f.write("\n".join(annotations))
            f.flush()
            cmd = f"sort {f.name} | uniq -c | sort -nr"
            stream = os.popen(cmd)
            self.out.write_text(stream.read())

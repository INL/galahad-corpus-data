"""Functions for fixing `<w>` and `<pc>` tokens."""

import re
import xml.etree.ElementTree as ET

from scripts.normalizer import et_ns, ns
from scripts.util.config import PUNCTUATION


def _normalize_w_that_should_be_pc(root: ET.Element) -> None:
    """Normalize <w> elements that should be <pc> because they contain punctuation."""
    for w in root.findall(".//tei:w", et_ns):
        text = "".join(w.itertext()).strip()
        if re.fullmatch(PUNCTUATION, text):
            # make an exeption for pos tags like RES (%) & NUM (1/3)
            pos = w.get("pos", "")
            if "RES" in pos or "NUM" in pos:
                continue
            # make an exception for <w> with <join> child
            if w.find("tei:join", et_ns) is not None:
                continue
            # change tag to pc
            w.tag = f"{ns['tei']}pc"
            # set @pos to PC
            w.set("pos", "PC")
            # set @lemma to the text content (stripped)
            w.set("lemma", text)
            # if the <pc> contains a <seg>, remove it but keep its text content
            seg = w.find("tei:seg", et_ns)
            if seg is not None:
                seg_text = "".join(seg.itertext()).strip()
                # remove seg but keep text
                w.remove(seg)
                w.text = (w.text or "") + seg_text
            # if it contains a <fs>, remove it completely
            fs = w.find("tei:fs", et_ns)
            if fs is not None:
                w.remove(fs)


def _normalize_pc(root: ET.Element) -> None:
    """
    Normalize `<pc>` elements to have @pos="PC" and @lemma set to its text.

    Raises:
        ValueError: empty <pc>.
    """
    for pc in root.findall(".//tei:pc", et_ns):
        # set @pos to PC
        pc.set("pos", "PC")
        # set @lemma to the text content (stripped)
        text = "".join(pc.itertext()).strip()
        if not text:
            raise ValueError("<pc> element has empty text")
        pc.set("lemma", text)


def normalize_tokens(root: ET.Element) -> None:
    """Run all token normalization functions."""
    _normalize_w_that_should_be_pc(root)
    _normalize_pc(root)

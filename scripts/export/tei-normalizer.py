#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config.config import PUNCTUATION

ns = {
    "xml": "{http://www.w3.org/XML/1998/namespace}",
    "tei": "{http://www.tei-c.org/ns/1.0}",
    "": "{http://www.tei-c.org/ns/1.0}",
}
et_ns = {k: v[1:-1] for k, v in ns.items()}

for k, v in et_ns.items():
    ET.register_namespace(k, v)


def normalize_root(root: ET.Element) -> bool:
    if root.tag not in [
        f"{ns['tei']}TEI",
        "TEI.2",
    ]:
        raise ValueError(f"Unexpected root tag {root.tag}")

    # normalize TEI.2 to TEI
    if root.tag == "TEI.2":
        root.tag = f"{ns['tei']}TEI"
        return True  # changed

    return False  # not changed


def normalize_root_xml_id(root: ET.Element):
    # Check for an xml:id on the root
    if f"{ns['xml']}id" not in root.attrib:
        # try to find it in text/@xml:id
        text_elem = root.find(".//tei:text[@xml:id]", et_ns)
        xmlid = (
            text_elem.get("{" + ns["xml"] + "}id") if text_elem is not None else None
        )
        if xmlid is None:
            # use <idno type="pid">UUID</idno> if present
            idno_elem = root.find(".//tei:idno[@type='pid']", et_ns)
            xmlid = idno_elem.text if idno_elem is not None else None
            if xmlid is None:
                # use <interpGrp type="pid"><interp>UUID</interp></interpGrp>
                interp = root.find(".//tei:interpGrp[@type='pid']/tei:interp", et_ns)
                xmlid = interp.text if interp is not None else None
                # might be in interp/@value
                if xmlid is None and interp is not None:
                    xmlid = interp.get("value")

                if xmlid is None:
                    # use cit/@xml:id if present
                    cit_elem = root.find(".//tei:cit", et_ns)
                    xmlid = cit_elem.get(f"{ns['xml']}id")

        if xmlid is None:
            raise ValueError("No xml:id found for root element")
        root.set(f"{ns['xml']}id", xmlid)


def normalize_text_body(root: ET.Element):
    # we expect two scenarios:
    # the root contains <teiHeader> and <text>...</text>
    # or the root contains <teiHeader> and <cit>...</cit>

    children = list(root)
    if len(children) != 2:
        raise ValueError("Unexpected structure")
    if children[0].tag != f"{ns['tei']}teiHeader":
        raise ValueError("First child is not <teiHeader>")
    if children[1].tag == f"{ns['tei']}text":
        return
    if children[1].tag != f"{ns['tei']}cit":
        raise ValueError(f"Second child is neither <text> nor <cit>: {children[1].tag}")

    # wrap the <cit> into <text><body>...</body></text>
    cit = root.find(".//tei:cit", et_ns)
    if cit is None:
        raise ValueError("No <cit> found")
    # remove cit from root
    root.remove(cit)
    # create new elements
    text_elem = ET.Element(f"{ns['tei']}text")
    body_elem = ET.Element(f"{ns['tei']}body")
    # move cit into body, and body into text
    body_elem.append(cit)
    text_elem.append(body_elem)
    # append text to root
    root.append(text_elem)


def normalize_pc(root: ET.Element):
    # Normalize <pc> elements to have @pos="PC" and @lemma set to its text
    for pc in root.findall(".//tei:pc", et_ns):
        # set @pos to PC
        pc.set("pos", "PC")
        # set @lemma to the text content (stripped)
        text = "".join(pc.itertext()).strip()
        if text == "":
            raise ValueError("<pc> element has empty text")
        pc.set("lemma", text)


def normalize_w_that_should_be_pc(root: ET.Element):
    # Normalize <w> elements that should be <pc>
    for w in root.findall(".//tei:w", et_ns):
        text = "".join(w.itertext()).strip()
        if re.fullmatch(PUNCTUATION, text):
            # make an exeption for pos tags like RES (%) & NUM (1/3)
            pos = w.get("pos", "")
            if "RES" in pos or "NUM" in pos:
                continue
            # change tag to pc
            w.tag = f"{ns['tei']}pc"
            # set @pos to PC
            w.set("pos", "PC")
            # set @lemma to the text content (stripped)
            w.set("lemma", text)


def normalize_div_type_notes(root: ET.Element):
    # Normalize <div> elements with @type="notes" to simply <note>
    for div in root.findall(".//tei:div[@type='notes']", et_ns):
        div.tag = f"{ns['tei']}note"
        if "type" in div.attrib:
            del div.attrib["type"]


def put_unanalyzed_words_in_note(root: ET.Element):
    """
    Put redactional commentary (i.e. <w> with empty @lemma often surrounded by two <pc>'s) into <note> elements.
    """

    parent_map = {c: p for p in root.iter() for c in p}

    # Get all <w> with empty @lemma and <pc> (not already inside <note>)
    w_elements = [
        el
        for el in root.findall(".//tei:w", et_ns)
        if parent_map[el].tag != f"{ns['tei']}note" and el.get("lemma", "") == ""
    ]
    pc_elements = [
        el
        for el in root.findall(".//tei:pc", et_ns)
        if parent_map[el].tag != f"{ns['tei']}note"
    ]
    elements = sorted(
        w_elements + pc_elements, key=lambda x: list(parent_map[x]).index(x)
    )

    # keep track of processed elements
    done: set[ET.Element] = set()

    for el in elements:
        if el in done:
            continue
        # determine index of this element in its parent
        p = parent_map[el]
        children = list(p)
        i = children.index(el)

        # start a potential group
        group = [el]
        j = i + 1
        # collect following siblings that are in elements
        while j < len(children) and children[j] in elements:
            group.append(children[j])
            j += 1

        # only proceed if the group has at least two elements and one of them is a <w>
        if len(group) >= 2 and any(g.tag == f"{ns['tei']}w" for g in group):
            # create a <note> element and move the group into it
            note = ET.Element(f"{ns['tei']}note")
            p.insert(i, note)
            for g in group:
                p.remove(g)
                note.append(g)
                done.add(g)  # mark as done


def put_last_enz_in_note(root: ET.Element):
    """If the last <w> of the document has text 'enz' and no lemma, put it into a <note>."""
    parent_map = {c: p for p in root.iter() for c in p}
    w_elements = root.findall(".//tei:w", et_ns)
    if not w_elements:
        return
    last_w = w_elements[-1]
    text = "".join(last_w.itertext()).strip()
    if text.lower() in ["enz.", "enz", "enz.,"] and last_w.get("lemma") == "":
        p = parent_map[last_w]
        # create a <note> element and move last_w into it
        note = ET.Element(f"{ns['tei']}note")
        p.insert(len(p), note)
        p.remove(last_w)
        note.append(last_w)


def check_or_update(file: Path):
    tree = ET.parse(file)
    root = tree.getroot()

    normalize_root(root)

    # normalize namespace issues by rewriting and reparsing
    write(tree, file)
    tree = ET.parse(file)
    root = tree.getroot()

    normalize_root_xml_id(root)
    normalize_text_body(root)
    normalize_w_that_should_be_pc(root)
    normalize_pc(root)
    normalize_div_type_notes(root)

    put_unanalyzed_words_in_note(root)
    put_last_enz_in_note(root)

    write(tree, file)


def write(tree: ET.ElementTree, file: Path):
    ET.indent(tree, space="  ")
    tree.write(
        file,
        encoding="utf-8",
        xml_declaration=True,
    )


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Lancelot TEI XML validator",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-r", action="store_true", help="Recursive")
    parser.add_argument("input", type=Path, help="xml file or dir")
    args = parser.parse_args()

    if args.input.is_file() and args.r:
        raise ValueError("Cannot use -r with a single file input")

    if args.input.is_file():
        check_or_update(args.input)
        print(f"Normalized {args.input}")
        exit(0)

    if args.input.is_dir():
        files = list(args.input.rglob("*.xml") if args.r else args.input.glob("*.xml"))
        for f in files:
            try:
                check_or_update(f)
            except Exception as e:
                print(f"Error processing {f}:")
                raise e
        print(f"Normalized {len(files)} files")

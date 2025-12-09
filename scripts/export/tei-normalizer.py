#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import re
import xml.etree.ElementTree as ET

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
                    cit_elem = root.find(".//cit")
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
    if children[0].tag != "{http://www.tei-c.org/ns/1.0}teiHeader":
        raise ValueError("First child is not <teiHeader>")
    if children[1].tag == "{http://www.tei-c.org/ns/1.0}text":
        return
    if children[1].tag != "cit":
        raise ValueError(f"Second child is neither <text> nor <cit>: {children[1].tag}")

    # wrap the <cit> into <text><body>...</body></text>
    cit = root.find(".//cit")
    if cit is None:
        raise ValueError("No <cit> found")
    # remove cit from root
    root.remove(cit)
    # create new elements
    text_elem = ET.Element("{http://www.tei-c.org/ns/1.0}text")
    body_elem = ET.Element("{http://www.tei-c.org/ns/1.0}body")
    # move cit into body, and body into text
    body_elem.append(cit)
    text_elem.append(body_elem)
    # append text to root
    root.append(text_elem)


def normalize_pc(root: ET.Element):
    # Normalize <pc> elements to have a space after punctuation if missing
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
        PUNCTUATION = r"[][…\.,;!?¶&'„│—\":]"
        if re.fullmatch(PUNCTUATION, text):
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


def check_or_update(file: Path):
    tree = ET.parse(file)
    root = tree.getroot()

    # root normalization is special in that the others relay on a <TEI> root
    changed = normalize_root(root)
    if changed:
        # write and reparse
        write(tree, file)
        tree = ET.parse(file)
        root = tree.getroot()

    normalize_root_xml_id(root)
    normalize_text_body(root)
    normalize_pc(root)
    normalize_div_type_notes(root)
    normalize_w_that_should_be_pc(root)

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
    parser.add_argument("dir", type=Path, help="Directory containing .xml files")
    parser.add_argument("-r", action="store_true", help="Recursive")
    args = parser.parse_args()

    files = args.dir.rglob("*.xml") if args.r else args.dir.glob("*.xml")
    for xml_file in files:
        try:
            check_or_update(xml_file)
        except Exception as e:
            print(f"Error processing {xml_file}:")
            raise e

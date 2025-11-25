#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
import xml.etree.ElementTree as ET

ns = {
    "xml": "http://www.w3.org/XML/1998/namespace",
    "tei": "http://www.tei-c.org/ns/1.0",
}

for k, v in ns.items():
    ET.register_namespace(k, v)

ET.register_namespace("", ns["tei"])


def check_or_update(file: Path):
    tree = ET.parse(file)
    root = tree.getroot()

    # expect root to be <TEI> or <TEI.2>
    if root.tag not in [
        "{http://www.tei-c.org/ns/1.0}TEI",
        "TEI.2",
    ]:
        raise ValueError(f"Unexpected root tag {root.tag} in {file}")

    # if it is <TEI.2>, change to <TEI>
    if root.tag == "TEI.2":
        root.tag = "{http://www.tei-c.org/ns/1.0}TEI"
        # write back to file
        ET.indent(tree, space="  ")
        tree.write(
            file,
            encoding="utf-8",
            xml_declaration=True,
        )
        print(f"Updated root tag to <TEI> in {file}")
        # reload tree
        tree = ET.parse(file)
        root = tree.getroot()

    # Check for an xml:id on the root
    if "{" + ns["xml"] + "}id" not in root.attrib:
        # try to find it in text/@xml:id
        text_elem = root.find(".//tei:text[@xml:id]", ns)
        xmlid = (
            text_elem.get("{" + ns["xml"] + "}id") if text_elem is not None else None
        )
        if xmlid is None:
            # use <idno type="pid">UUID</idno> if present
            idno_elem = root.find(".//tei:idno[@type='pid']", ns)
            xmlid = idno_elem.text if idno_elem is not None else None
            if xmlid is None:
                # use <interpGrp type="pid"><interp>UUID</interp></interpGrp>
                interp = root.find(".//tei:interpGrp[@type='pid']/tei:interp", ns)
                xmlid = interp.text if interp is not None else None
                # might be in interp/@value
                if xmlid is None and interp is not None:
                    xmlid = interp.get("value")

                if xmlid is None:
                    # use cit/@xml:id if present
                    cit_elem = root.find(".//cit[@xml:id]", ns)
                    xmlid = cit_elem.get("{" + ns["xml"] + "}id")
        root.set("{" + ns["xml"] + "}id", xmlid)
        # write back to file
        ET.indent(tree, space="  ")
        tree.write(
            file,
            encoding="utf-8",
            xml_declaration=True,
        )
        print(f"Added xml:id to root in {file}")
        # reload tree
        tree = ET.parse(file)
        root = tree.getroot()

    # we expect two scenarios:
    # the root contains <teiHeader> and <text>...</text>
    # or the root contains <teiHeader> and <cit>...</cit>

    children = list(root)
    if len(children) != 2:
        raise ValueError(f"Unexpected structure in {file}")
    if children[0].tag != "{http://www.tei-c.org/ns/1.0}teiHeader":
        raise ValueError(f"First child is not <teiHeader> in {file}")
    if children[1].tag == "{http://www.tei-c.org/ns/1.0}text":
        return
    if children[1].tag != "{http://www.tei-c.org/ns/1.0}cit":
        raise ValueError(
            f"Second child is neither <text> nor <cit> in {file}: {children[1].tag}"
        )

    # wrap the <cit> into <text><body>...</body></text>
    cit = root.find("{http://www.tei-c.org/ns/1.0}cit", ns)
    if cit is None:
        raise ValueError(f"No <cit> found in {file}")
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
    # write back to same file
    # pretty print
    ET.indent(tree, space="  ")
    tree.write(
        file,
        encoding="utf-8",
        xml_declaration=True,
    )
    print(f"Wrapped <cit> into <text><body> in {file}")


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

#!/usr/bin/env python3

import re
import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

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
                    xmlid = (
                        cit_elem.get(f"{ns['xml']}id") if cit_elem is not None else None
                    )
                    if xmlid is not None:
                        xmlid = f"pid_{xmlid}"

        if xmlid is None:
            raise ValueError("No xml:id found for root element")
        # set it
        root.set(f"{ns['xml']}id", xmlid)

    # now, retrieve the xml id once more, either just added or already present
    xmlid = root.get(f"{ns['xml']}id")
    # if xml id matches UUID regex
    if re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        xmlid,
    ):
        xmlid = f"pid_{xmlid}"
        # readd
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


def remove_word_illegal_attributes(root: ET.Element):
    # remove illegal attributes
    illegal_attrs = {
        (".//tei:w", ".//tei:pc"): [
            "lexicon",
            "corresp",
            "changed",
            "gloss",
            "misAlignment",
            "feest",
            "lemmaRef",
            "time",
            "valid",
            "originalContent",
            "ctag",
            "mform",
            "org",
        ],
        (".//tei:teiHeader",): ["type"],
        (".//tei:xr",): ["extent"],
        (".//tei:s",): ["fixed"],
    }

    for tag_list, illegal_attrs in illegal_attrs.items():
        nodes = []
        for tag in tag_list:
            nodes.extend(root.findall(tag, et_ns))
        for node in nodes:
            for attr in illegal_attrs:
                if attr in node.attrib:
                    del node.attrib[attr]


def fixup_cit(root: ET.Element):
    # Some <cit> elements contain a <date> as child.
    # Wrap this in <note>
    for cit in root.findall(".//tei:cit", et_ns):
        date = cit.find("tei:date", et_ns)

        if date is None:
            continue

        note = ET.Element(f"{ns['tei']}note")
        ab = ET.SubElement(note, f"{ns['tei']}ab")
        ab.append(date)
        cit.insert(0, note)
        # remove date from its original position
        cit.remove(date)
        # move @timeSpan to @extent
        if "timeSpan" in date.attrib:
            date.set("extent", date.get("timeSpan"))
            del date.attrib["timeSpan"]
        # next, add a interpGrp and interp for each attribute of cit
        for attr in ["lemma", "pos", "sense-id", "modern-lemma", "entry-id"]:
            if attr in cit.attrib:
                attr_to_interp(cit, attr, ab)

        # remove partition
        del cit.attrib["partition"]
        # every cit also contains at q with at least one <w> with @sense-id, we can move it to @lemmaRef
        q = cit.find("tei:q", et_ns)
        for w in q.findall("tei:w", et_ns):
            if "sense-id" in w.attrib:
                w.set("lemmaRef", w.get("sense-id"))
                del w.attrib["sense-id"]


def attr_to_interp(cit: ET.Element, attr: str, ab: ET.Element):
    interpGrp = ET.SubElement(ab, f"{ns['tei']}interpGrp", type=attr)
    interp = ET.SubElement(interpGrp, f"{ns['tei']}interp")
    interp.text = cit.get(attr)
    del cit.attrib[attr]


def move_licence_to_p(root: ET.Element):
    # <publicationStmt> <availability> <licence> text </licence> </availability> </publicationStmt>
    # should be: <publicationStmt> <p> text </p> </publicationStmt>
    publicationStmt = root.find(".//tei:publicationStmt", et_ns)
    if publicationStmt is not None:
        availability = publicationStmt.find("tei:availability", et_ns)
        if availability is not None:
            licence = availability.find("tei:licence", et_ns)
            if licence is not None:
                # create a <p> element and move the text of <licence> into it
                p = ET.Element(f"{ns['tei']}p")
                p.text = licence.text
                publicationStmt.append(p)
                # remove the original <availability> element
                publicationStmt.remove(availability)

            # alternatively, <availability> contains some <p>'s
            # first check whether availability truly only contains <p>
            for child in availability:
                if child.tag != f"{ns['tei']}p":
                    return  # if not, do nothing

            # move these and then remove <availability)
            for child in availability:
                publicationStmt.append(child)
            publicationStmt.remove(availability)

            # and in this case, rename <idno> to <p> as well
            for idno in publicationStmt.findall("tei:idno", et_ns):
                idno.tag = f"{ns['tei']}p"


def remove_couranten_sourceDesc_text(root: ET.Element):
    # sourceDesc may contain text directly, often a sibling of <interpGrp>
    # move this text into a <p> element (sibling of the <interpGrp>)
    sourceDesc = root.find(".//tei:sourceDesc", et_ns)
    if sourceDesc is not None:
        # get the tail of the interpGrp, which is the text after the last child element of sourceDesc
        listBibl = sourceDesc.find("tei:listBibl", et_ns)
        if listBibl is not None:
            text = listBibl.tail
            if text:
                # remove the original text from sourceDesc
                listBibl.tail = None


def remove_empty_i_and_b(root: ET.Element):
    # remove <i> and <b> elements that have no text and no children
    # iterate so we have the parent. Need parent to remove the element if needed (since .getparent() is not supported in xml.etree)
    parent_map = {c: p for p in root.iter() for c in p}
    for el in root.findall(".//tei:i", et_ns) + root.findall(".//tei:b", et_ns):
        if (el.text is None or el.text.strip() == "") and len(el) == 0:
            parent = parent_map[el]
            parent.remove(el)


def remove_w_from_interpGrp(root: ET.Element):
    # transform <interpGrp> <interp> <w> text </w> </interp> </interpGrp>
    # to <interpGrp> <interp>text</interp> </interpGrp>
    for interpGrp in root.findall(".//tei:interpGrp", et_ns):
        for interp in interpGrp.findall("tei:interp", et_ns):
            w = interp.find("tei:w", et_ns)
            if w is not None:
                text = "".join(w.itertext()).strip()
                interp.text = text
                interp.remove(w)


def move_text_in_pb_to_n(root: ET.Element):
    # move <pb> text </pb> to <pb n="text"/>
    for pb in root.findall(".//tei:pb", et_ns):
        if pb.text:
            pb.set("n", pb.text)
            pb.text = None


def put_lonely_p_in_div(root: ET.Element):
    # some <div>'s contain multiple other <div>'s and <p>'s with text. Move these <p> into a <div>'s inside the parent <div>.
    for div in root.findall(".//tei:div", et_ns):
        for p in div.findall("tei:p", et_ns):
            if p is not None and len(div.findall("tei:div", et_ns)) > 0:
                # create a new <div> and move the <p> into it
                child_div = ET.Element(f"{ns['tei']}div")
                child_div.append(p)
                div.append(child_div)
                # remove the original <p> from div
                div.remove(p)


def move_sourceDesc(root: ET.Element):
    # transform <teiHeader> <sourceDesc> ... </sourceDesc> </teiHeader>
    # to <teiHeader> <fileDesc> <sourceDesc> ... </sourceDesc> </fileDesc> </teiHeader>
    # note that fileDesc may already be present, in which case we need to move sourceDesc into it
    # and if there is already a sourceDesc in fileDesc, we delete it and prefer the one outside of fileDesc
    teiHeader = root.find(".//tei:teiHeader", et_ns)
    if teiHeader is not None:
        sourceDesc = teiHeader.find("tei:sourceDesc", et_ns)
        if sourceDesc is not None:
            fileDesc = teiHeader.find("tei:fileDesc", et_ns)
            if fileDesc is None:
                fileDesc = ET.Element(f"{ns['tei']}fileDesc")
                teiHeader.append(fileDesc)
            existing_sourceDesc = fileDesc.find("tei:sourceDesc", et_ns)
            if existing_sourceDesc is not None:
                fileDesc.remove(existing_sourceDesc)
            # move sourceDesc into fileDesc
            teiHeader.remove(sourceDesc)
            fileDesc.append(sourceDesc)


def move_listBibl_id_to_xml_id(root: ET.Element):
    # if <listBibl> has an @id, turn it into an @xml:id
    for listBibl in root.findall(".//tei:listBibl", et_ns):
        if "id" in listBibl.attrib:
            listBibl.set(f"{ns['xml']}id", listBibl.get("id"))
            del listBibl.attrib["id"]


def move_interp_value_to_text(root: ET.Element):
    # if <interp> has a @value, move it to the text content of the element
    for interp in root.findall(".//tei:interp", et_ns):
        if "value" in interp.attrib:
            interp.text = interp.get("value")
            del interp.attrib["value"]


def replace_hyphen_with_hyphen(root: ET.Element):
    # replace element <hyphen /> with actual "-"

    parent_map = {c: p for p in root.iter() for c in p}

    for hyphen in root.findall(".//tei:hyphen", et_ns):
        parent = parent_map.get(hyphen)
        if parent is not None:
            # insert a text node with "-" before the hyphen element
            index = list(parent).index(hyphen)
            if index == 0:
                parent.text = (parent.text or "") + "-"
            else:
                prev = parent[index - 1]
                prev.tail = (prev.tail or "") + "-"
            # remove the hyphen element
            parent.remove(hyphen)


def remove_nolink(root: ET.Element):
    # remove <nolink> elements
    parent_map = {c: p for p in root.iter() for c in p}
    for nolink in root.findall(".//tei:nolink", et_ns):
        parent = parent_map.get(nolink)
        if parent is not None:
            parent.remove(nolink)


def rename_old_pos_to_type(root: ET.Element):
    # rename @old_pos to @type on <w> and <pc> elements
    for el in root.findall(".//tei:w", et_ns) + root.findall(".//tei:pc", et_ns):
        if "old_pos" in el.attrib:
            el.set("type", el.get("old_pos"))
            del el.attrib["old_pos"]


def move_bron_to_sourceDesc(root: ET.Element):
    # move <bron> elements from <teiHeader> to <sourceDesc> renamed as <p>
    teiHeader = root.find(".//tei:teiHeader", et_ns)
    if teiHeader is not None:
        bron = teiHeader.find("tei:bron", et_ns)
        if bron is not None:
            fileDesc = teiHeader.find("tei:fileDesc", et_ns)
            if fileDesc is not None:
                sourceDesc = fileDesc.find("tei:sourceDesc", et_ns)
                if sourceDesc is not None:
                    # create a <bibl> element and move the text of <bron> into it
                    bibl = ET.Element(f"{ns['tei']}bibl")
                    bibl.text = bron.text
                    sourceDesc.append(bibl)
                    # remove the original <bron> element
                    teiHeader.remove(bron)


def move_xr_to_cit_in_note(root: ET.Element):
    # transform <w> <xr> ... </xr> </w>
    # to <w> <note> <cit> <xr> </xr> </cit> </note> </w>
    for w in root.findall(".//tei:w", et_ns):
        xr = w.find("tei:xr", et_ns)
        if xr is not None:
            note = ET.SubElement(w, f"{ns['tei']}note")
            cit = ET.SubElement(note, f"{ns['tei']}cit")
            cit.append(xr)
            w.remove(xr)


def create_interpGrp_for_dictionary_xr(root: ET.Element):
    # transform:
    # <xr>
    # <ref citaatId="13531">
    #     <modern_lemma>ook</modern_lemma>
    #     <lemma>ooc</lemma>
    #     <def>ook; ook wel</def>
    #     <pos>bw.</pos>
    # </ref>
    # </xr>
    # to
    # <xr>
    # <ref>
    #     <interpGrp>
    #         <interp type="citaatId">13531</interp>
    #         <interp type="modern_lemma">ook</interp>
    #         <interp type="lemma">ooc</interp>
    #         <interp type="def">ook; ook wel</interp>
    #         <interp type="pos">bw.</interp>
    #     </interpGrp>
    # </ref>
    # </xr>
    for xr in root.findall(".//tei:xr", et_ns):
        for ref in xr.findall("tei:ref", et_ns):
            interpGrp = ET.SubElement(ref, f"{ns['tei']}interpGrp")

            for child in list(ref):
                if child.tag in [
                    f"{ns['tei']}modern_lemma",
                    f"{ns['tei']}lemma",
                    f"{ns['tei']}def",
                    f"{ns['tei']}pos",
                ]:
                    interp = ET.SubElement(
                        interpGrp,
                        f"{ns['tei']}interp",
                        type=child.tag[len(ns["tei"]) :],
                    )
                    interp.text = child.text
                    ref.remove(child)

            citaatId = ref.get("citaatId")
            if citaatId is not None:
                interp = ET.SubElement(interpGrp, f"{ns['tei']}interp", type="citaatId")
                interp.text = citaatId
                del ref.attrib["citaatId"]


def remove_bron_not_found(root: ET.Element):
    # simply remove <bron_not_found> elements in teiHeader
    teiHeader = root.find(".//tei:teiHeader", et_ns)
    if teiHeader is not None:
        for bron_not_found in teiHeader.findall("tei:bron_not_found", et_ns):
            teiHeader.remove(bron_not_found)


def move_fs_xml_id_to_n(root: ET.Element):
    # if <fs> has an @xml:id, move it to @n
    for fs in root.findall(".//tei:fs", et_ns):
        if f"{ns['xml']}id" in fs.attrib:
            fs.set("n", fs.get(f"{ns['xml']}id"))
            del fs.attrib[f"{ns['xml']}id"]


def remove_fs_in_empty_pos_w(root: ET.Element):
    # if a <w> has @pos="" and contains an <fs>, remove the <fs>
    for w in root.findall(".//tei:w", et_ns):
        if w.get("pos") == "":
            fs = w.find("tei:fs", et_ns)
            if fs is not None:
                w.remove(fs)


def fixup_w_xml_id(root: ET.Element):
    # some <w> and <pc> have an @xml:id that starts with a number
    # prefix them with 'w'
    for w in root.findall(".//tei:w", et_ns) + root.findall(".//tei:pc", et_ns):
        xml_id = w.get(f"{ns['xml']}id")
        if xml_id is not None and re.match(r"^[0-9]", xml_id):
            w.set(f"{ns['xml']}id", f"w{xml_id}")


def remove_empty_interpGrp(root: ET.Element):
    parent_map = {c: p for p in root.iter() for c in p}
    for interpGrp in root.findall(".//tei:interpGrp", et_ns):
        if len(interpGrp) == 0 and (
            interpGrp.text is None or interpGrp.text.strip() == ""
        ):
            parent = parent_map.get(interpGrp)
            if parent is not None:
                parent.remove(interpGrp)


def move_sourceDesc_p_to_bibl(root: ET.Element):
    # if <sourceDesc> contains at least one <listBibl>
    # rename all <p> to <bibl>
    sourceDesc = root.find(".//tei:sourceDesc", et_ns)
    if sourceDesc is not None and sourceDesc.find("tei:listBibl", et_ns) is not None:
        for p in sourceDesc.findall("tei:p", et_ns):
            p.tag = f"{ns['tei']}bibl"


def move_biblScope_xref_attrs(root: ET.Element):
    # transform <biblScope> <xref to="..." from="..."/> </biblScope>
    # to <biblScope to="..." from="..." />
    for biblScope in root.findall(".//tei:biblScope", et_ns):
        xref = biblScope.find("tei:xref", et_ns)
        if xref is not None:
            for attr in ["to", "from"]:
                if attr in xref.attrib:
                    biblScope.set(attr, xref.get(attr))
            biblScope.remove(xref)


def fixup_change_resp(root: ET.Element):
    # transform: <change> <respStmt> <name> ... </name> </respStmt> </change>
    # to: <change resp="..." />
    teiHeader = root.find(".//tei:teiHeader", et_ns)
    if teiHeader is not None:
        for change in teiHeader.findall(".//tei:change", et_ns):
            respStmt = change.find("tei:respStmt", et_ns)
            if respStmt is not None:
                name = respStmt.find("tei:name", et_ns)
                if name is not None and name.text:
                    change.set("resp", name.text)
                # remove the original respStmt
                change.remove(respStmt)

            # additionally, unwrap the text in <item>
            item = change.find("tei:item", et_ns)
            if item is not None and item.text:
                change.text = item.text
                change.remove(item)


def remove_empty_type_in_w_and_pc(root: ET.Element):
    # remove @type if empty in <w> and <pc>
    for el in root.findall(".//tei:w", et_ns) + root.findall(".//tei:pc", et_ns):
        if el.get("type") == "":
            del el.attrib["type"]


def check_or_update(file: Path):
    tree = ET.parse(file)
    root = tree.getroot()

    normalize_root(root)

    # normalize namespace issues by rewriting and reparsing
    write(tree, file)
    tree = ET.parse(file)
    root = tree.getroot()

    # normalization focussed on editing text
    normalize_root_xml_id(root)
    normalize_text_body(root)
    normalize_w_that_should_be_pc(root)
    normalize_pc(root)
    normalize_div_type_notes(root)

    # normalization focussed on TEI validation
    remove_word_illegal_attributes(root)
    fixup_cit(root)
    move_licence_to_p(root)
    remove_couranten_sourceDesc_text(root)
    remove_empty_i_and_b(root)
    remove_w_from_interpGrp(root)
    move_text_in_pb_to_n(root)
    put_lonely_p_in_div(root)
    move_sourceDesc(root)
    move_listBibl_id_to_xml_id(root)
    move_interp_value_to_text(root)
    replace_hyphen_with_hyphen(root)
    remove_nolink(root)
    rename_old_pos_to_type(root)
    move_bron_to_sourceDesc(root)
    move_xr_to_cit_in_note(root)
    create_interpGrp_for_dictionary_xr(root)
    remove_bron_not_found(root)
    move_fs_xml_id_to_n(root)
    remove_fs_in_empty_pos_w(root)
    fixup_w_xml_id(root)
    remove_empty_interpGrp(root)
    move_sourceDesc_p_to_bibl(root)
    move_biblScope_xref_attrs(root)
    fixup_change_resp(root)
    remove_empty_type_in_w_and_pc(root)

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

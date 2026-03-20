import xml.etree.ElementTree as ET

ns = {
    "xml": "{http://www.w3.org/XML/1998/namespace}",
    "tei": "{http://www.tei-c.org/ns/1.0}",
    "": "{http://www.tei-c.org/ns/1.0}",
}
et_ns = {k: v[1:-1] for k, v in ns.items()}

for k, v in et_ns.items():
    ET.register_namespace(k, v)

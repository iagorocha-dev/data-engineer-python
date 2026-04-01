from __future__ import annotations

import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

from src.viacep.models import Address


def export_to_json(output_path: Path, addresses: list[Address]) -> None:
    """
    Exporta endereços para arquivo JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [address.__dict__ for address in addresses]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_to_xml(output_path: Path, addresses: list[Address]) -> None:
    """
    Exporta endereços para arquivo XML.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root = Element("addresses")

    for address in addresses:
        addr_el = SubElement(root, "address")

        for key, value in address.__dict__.items():
            field = SubElement(addr_el, key)
            field.text = "" if value is None else str(value)

    tree = ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
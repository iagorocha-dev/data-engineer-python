from pathlib import Path

from src.io.exporters import export_to_json, export_to_xml
from src.viacep.models import Address


def test_export_to_json_creates_file_with_expected_content(tmp_path: Path) -> None:
    output_file = tmp_path / "addresses.json"

    addresses = [
        Address(
            cep="01310100",
            logradouro="Avenida Paulista",
            bairro="Bela Vista",
            localidade="São Paulo",
            uf="SP",
            ibge="3550308",
            gia=None,
            ddd="11",
            siafi="7107",
        )
    ]

    export_to_json(output_file, addresses)

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert '"cep": "01310100"' in content
    assert '"localidade": "São Paulo"' in content
    assert '"uf": "SP"' in content


def test_export_to_xml_creates_file_with_expected_content(tmp_path: Path) -> None:
    output_file = tmp_path / "addresses.xml"

    addresses = [
        Address(
            cep="01310100",
            logradouro="Avenida Paulista",
            bairro="Bela Vista",
            localidade="São Paulo",
            uf="SP",
            ibge="3550308",
            gia=None,
            ddd="11",
            siafi="7107",
        )
    ]

    export_to_xml(output_file, addresses)

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "<addresses>" in content
    assert "<address>" in content
    assert "<cep>01310100</cep>" in content
    assert "<localidade>São Paulo</localidade>" in content
    assert "<uf>SP</uf>" in content
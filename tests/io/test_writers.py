from pathlib import Path

from src.io.writers import write_errors_csv


def test_write_errors_csv_creates_file_with_expected_content(tmp_path: Path) -> None:
    output_file = tmp_path / "errors.csv"

    errors = [
        {
            "cep": "88888888",
            "error_type": "not_found",
            "status_code": 200,
            "message": "CEP não encontrado",
        }
    ]

    write_errors_csv(output_file, errors)

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "cep,error_type,status_code,message" in content
    assert "88888888,not_found,200,CEP não encontrado" in content
from pathlib import Path

from src.io.writers import append_errors_csv, load_error_ceps, write_errors_csv


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


def test_append_errors_csv_appends_without_duplicating_header(tmp_path: Path) -> None:
    output_file = tmp_path / "errors.csv"

    append_errors_csv(
        output_file,
        [
            {
                "cep": "11111111",
                "error_type": "not_found",
                "status_code": 200,
                "message": "primeiro",
            }
        ],
    )
    append_errors_csv(
        output_file,
        [
            {
                "cep": "22222222",
                "error_type": "http_error",
                "status_code": 500,
                "message": "segundo",
            }
        ],
    )

    lines = output_file.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "cep,error_type,status_code,message"
    assert lines.count("cep,error_type,status_code,message") == 1
    assert any("11111111,not_found,200,primeiro" == line for line in lines)
    assert any("22222222,http_error,500,segundo" == line for line in lines)


def test_load_error_ceps_returns_empty_set_when_file_does_not_exist(tmp_path: Path) -> None:
    assert load_error_ceps(tmp_path / "missing.csv") == set()


def test_load_error_ceps_returns_unique_non_empty_ceps(tmp_path: Path) -> None:
    output_file = tmp_path / "errors.csv"
    output_file.write_text(
        "\n".join(
            [
                "cep,error_type,status_code,message",
                "11111111,not_found,200,primeiro",
                "22222222,http_error,500,segundo",
                "11111111,http_error,500,repetido",
                ",http_error,500,vazio",
            ]
        ),
        encoding="utf-8",
    )

    assert load_error_ceps(output_file) == {"11111111", "22222222"}

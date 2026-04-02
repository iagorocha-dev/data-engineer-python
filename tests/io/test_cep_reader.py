from pathlib import Path

import pandas as pd

from src.io.cep_reader import load_ceps


def test_load_ceps_returns_valid_and_invalid_rows(tmp_path: Path) -> None:
    input_file = tmp_path / "ceps.csv"

    df = pd.DataFrame(
        {
            "cep": [
                "01310-100",  # válido
                "08949617",   # válido
                "474177",     # vira 00474177 e continua válido
                "ABC",        # inválido
                None,         # inválido
            ]
        }
    )
    df.to_csv(input_file, index=False)

    valid_ceps, invalid_rows = load_ceps(str(input_file))

    assert "01310100" in valid_ceps
    assert "08949617" in valid_ceps
    assert "00474177" in valid_ceps
    assert len(invalid_rows) == 2
    assert invalid_rows[0]["error_type"] == "invalid_cep_format"


def test_load_ceps_removes_duplicates_preserving_order(tmp_path: Path) -> None:
    input_file = tmp_path / "ceps.csv"

    df = pd.DataFrame(
        {
            "cep": [
                "01310100",
                "01310-100",
                "08949617",
            ]
        }
    )
    df.to_csv(input_file, index=False)

    valid_ceps, invalid_rows = load_ceps(str(input_file))

    assert valid_ceps == ["01310100", "08949617"]
    assert invalid_rows == []


def test_load_ceps_raises_error_when_column_is_missing(tmp_path: Path) -> None:
    input_file = tmp_path / "ceps.csv"

    df = pd.DataFrame({"zipcode": ["01310100"]})
    df.to_csv(input_file, index=False)

    try:
        load_ceps(str(input_file))
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "coluna chamada 'cep'" in str(exc)
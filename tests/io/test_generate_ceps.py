from pathlib import Path

import pandas as pd

from src.io.generate_ceps import generate_unique_ceps, save_ceps_to_csv


def test_generate_unique_ceps_returns_expected_amount() -> None:
    ceps = generate_unique_ceps(100)

    assert len(ceps) == 100
    assert len(set(ceps)) == 100


def test_generate_unique_ceps_returns_only_eight_digit_strings() -> None:
    ceps = generate_unique_ceps(50)

    assert all(isinstance(cep, str) for cep in ceps)
    assert all(len(cep) == 8 for cep in ceps)
    assert all(cep.isdigit() for cep in ceps)


def test_save_ceps_to_csv_creates_file_with_expected_content(tmp_path: Path) -> None:
    output_file = tmp_path / "ceps.csv"
    ceps = ["01310100", "08949617", "00474177"]

    save_ceps_to_csv(ceps, output_file)

    assert output_file.exists()

    df = pd.read_csv(output_file, dtype={"cep": str})
    assert list(df.columns) == ["cep"]
    assert df["cep"].tolist() == ceps
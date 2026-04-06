from pathlib import Path

import pandas as pd
import pytest

from src.io.generate_ceps import (
    KNOWN_VALID_CEPS,
    build_cep_dataset,
    generate_random_unique_ceps,
    generate_unique_ceps,
    main,
    save_ceps_to_csv,
)


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


def test_generate_random_unique_ceps_ignores_excluded_values(monkeypatch) -> None:
    values = iter([12345678, 12345678, 87654321, 11223344])

    monkeypatch.setattr(
        "src.io.generate_ceps.random.randint",
        lambda start, end: next(values),
    )

    ceps = generate_random_unique_ceps(2, excluded={"12345678"})

    assert ceps == ["87654321", "11223344"]


def test_build_cep_dataset_raises_when_total_is_smaller_than_known_ceps() -> None:
    with pytest.raises(ValueError, match="não pode ser menor"):
        build_cep_dataset(len(KNOWN_VALID_CEPS) - 1)


def test_build_cep_dataset_includes_known_ceps_in_top_ten(monkeypatch) -> None:
    generated = [f"{i:08d}" for i in range(10000000, 10000007)]

    monkeypatch.setattr(
        "src.io.generate_ceps.generate_random_unique_ceps",
        lambda total, excluded: generated[:total],
    )
    monkeypatch.setattr("src.io.generate_ceps.random.shuffle", lambda values: None)

    dataset = build_cep_dataset(12)

    assert len(dataset) == 12
    assert set(KNOWN_VALID_CEPS).issubset(set(dataset[:10]))


def test_build_cep_dataset_raises_when_generated_size_is_wrong(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.io.generate_ceps.generate_random_unique_ceps",
        lambda total, excluded: ["11111111"],
    )
    monkeypatch.setattr("src.io.generate_ceps.random.shuffle", lambda values: None)

    with pytest.raises(ValueError, match="quantidade esperada"):
        build_cep_dataset(10)


def test_build_cep_dataset_raises_when_generated_list_has_duplicates(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.io.generate_ceps.generate_random_unique_ceps",
        lambda total, excluded: ["99999999"] * total,
    )
    monkeypatch.setattr("src.io.generate_ceps.random.shuffle", lambda values: None)

    with pytest.raises(ValueError, match="duplicados"):
        build_cep_dataset(10)


def test_generate_ceps_main_generates_dataset_and_saves_csv(monkeypatch, tmp_path: Path) -> None:
    generated_dataset = ["01001000", "01310100"]
    captured: dict[str, object] = {}

    monkeypatch.setattr("src.io.generate_ceps.setup_logging", lambda level: captured.setdefault("log_level", level))
    monkeypatch.setattr("src.io.generate_ceps.random.seed", lambda seed: captured.setdefault("seed", seed))
    monkeypatch.setattr("src.io.generate_ceps.build_cep_dataset", lambda total: generated_dataset)
    monkeypatch.setattr(
        "src.io.generate_ceps.save_ceps_to_csv",
        lambda ceps, output_path: captured.update({"ceps": ceps, "output_path": output_path}),
    )
    monkeypatch.setattr("src.io.generate_ceps.OUTPUT_PATH", tmp_path / "ceps.csv")
    monkeypatch.setattr("src.io.generate_ceps.TOTAL_CEPS", 2)

    main()

    assert captured["log_level"] == "INFO"
    assert captured["seed"] == 42
    assert captured["ceps"] == generated_dataset
    assert captured["output_path"] == tmp_path / "ceps.csv"

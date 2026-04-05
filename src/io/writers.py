from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ERROR_FIELDNAMES = ["cep", "error_type", "status_code", "message"]


def write_errors_csv(output_path: Path, errors: list[dict[str, Any]]) -> None:
    """
    Sobrescreve o arquivo CSV com os erros consolidados do processamento.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ERROR_FIELDNAMES)
        writer.writeheader()

        for error in errors:
            writer.writerow(
                {
                    "cep": error.get("cep", ""),
                    "error_type": error.get("error_type", ""),
                    "status_code": error.get("status_code", ""),
                    "message": error.get("message", ""),
                }
            )


def append_errors_csv(output_path: Path, errors: list[dict[str, Any]]) -> None:
    """
    Acrescenta erros ao CSV, criando header apenas se o arquivo não existir.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = output_path.exists()

    with output_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ERROR_FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        for error in errors:
            writer.writerow(
                {
                    "cep": error.get("cep", ""),
                    "error_type": error.get("error_type", ""),
                    "status_code": error.get("status_code", ""),
                    "message": error.get("message", ""),
                }
            )


def load_error_ceps(input_path: Path) -> set[str]:
    """
    Carrega os CEPs já registrados no arquivo de erros.
    """
    if not input_path.exists():
        return set()

    processed_ceps: set[str] = set()

    with input_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            cep = str(row.get("cep", "")).strip()
            if cep:
                processed_ceps.add(cep)

    return processed_ceps
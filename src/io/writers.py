from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_errors_csv(output_path: Path, errors: list[dict[str, Any]]) -> None:
    """
    Gera um arquivo CSV com os erros consolidados do processamento.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["cep", "error_type", "status_code", "message"]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
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
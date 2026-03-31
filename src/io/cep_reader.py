from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils.validators import is_valid_cep, normalize_cep


def load_ceps(csv_path: str) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Lê o CSV de CEPs, normaliza os valores e separa
    registros válidos e inválidos.

    Retorna:
      - valid_ceps: lista de CEPs válidos e únicos
      - invalid_rows: lista de erros padronizados
    """
    df = pd.read_csv(csv_path, dtype={"cep": str})

    if "cep" not in df.columns:
        raise ValueError("O CSV deve conter uma coluna chamada 'cep'.")

    valid_ceps: list[str] = []
    invalid_rows: list[dict[str, Any]] = []

    for raw_cep in df["cep"].tolist():
        normalized_cep = normalize_cep(raw_cep)

        if is_valid_cep(normalized_cep):
            valid_ceps.append(normalized_cep)
        else:
            invalid_rows.append(
                {
                    "cep": str(raw_cep),
                    "error_type": "invalid_cep_format",
                    "status_code": "",
                    "message": f"CEP inválido após normalização: '{normalized_cep}'",
                }
            )

    # Remove duplicados preservando ordem
    unique_valid_ceps: list[str] = []
    seen: set[str] = set()

    for cep in valid_ceps:
        if cep not in seen:
            seen.add(cep)
            unique_valid_ceps.append(cep)

    return unique_valid_ceps, invalid_rows
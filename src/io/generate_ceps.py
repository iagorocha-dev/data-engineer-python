from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


TOTAL_CEPS = 10_000
OUTPUT_PATH = Path("data/input/ceps.csv")
RANDOM_SEED = 42


def generate_unique_ceps(total: int) -> list[str]:
    """
    Gera uma lista de CEPs únicos com 8 dígitos.
    O objetivo aqui é produzir uma massa de entrada padronizada
    para o processamento do case.
    """
    random.seed(RANDOM_SEED)

    generated: set[str] = set()

    while len(generated) < total:
        cep = f"{random.randint(0, 99_999_999):08d}"
        generated.add(cep)

    return list(generated)


def save_ceps_to_csv(ceps: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({"cep": ceps})
    df.to_csv(output_path, index=False)


def main() -> None:
    ceps = generate_unique_ceps(TOTAL_CEPS)
    save_ceps_to_csv(ceps, OUTPUT_PATH)

    print(f"Arquivo gerado com sucesso em: {OUTPUT_PATH}")
    print(f"Total de CEPs gerados: {len(ceps)}")


if __name__ == "__main__":
    main()
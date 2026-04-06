from __future__ import annotations

import logging
import random
from pathlib import Path

import pandas as pd

from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)

TOTAL_CEPS = 10_000
OUTPUT_PATH = Path("data/input/ceps.csv")
RANDOM_SEED = 42

# 5 CEPs válidos conhecidos (Pontos Turisticos SP)
KNOWN_VALID_CEPS = [
    "01310100",  # Avenida Paulista - São Paulo/SP
    "01311000",  # Museu de Arte de São Paulo Assis Chateaubriand
    "04094050",  # Parque do Ibirapuera - São Paulo/SP
    "01001000",  # Teatro Municipal de São Paulo
    "01023000",  # Mercado Municipal de São Paulo
]


def generate_random_unique_ceps(total: int, excluded: set[str]) -> list[str]:
    """
    Gera CEPs aleatórios únicos com 8 dígitos, excluindo os já reservados.
    """
    generated: set[str] = set()

    while len(generated) < total:
        cep = f"{random.randint(0, 99_999_999):08d}"

        if cep in excluded:
            continue

        generated.add(cep)

    return list(generated)


def generate_unique_ceps(total: int) -> list[str]:
    """
    Mantém a API pública usada pelos testes e por chamadas externas.
    """
    return generate_random_unique_ceps(total, excluded=set())


def build_cep_dataset(total: int) -> list[str]:
    """
    Monta a lista final de CEPs garantindo que os CEPs conhecidos
    apareçam dentro das 20 primeiras posições.
    """
    if total < len(KNOWN_VALID_CEPS):
        raise ValueError(
            "O total de CEPs não pode ser menor que a quantidade de CEPs conhecidos."
        )

    reserved = set(KNOWN_VALID_CEPS)
    remaining_total = total - len(KNOWN_VALID_CEPS)

    random_ceps = generate_random_unique_ceps(remaining_total, excluded=reserved)

    # Garantir que os 5 conhecidos fiquem dentro do top 10
    top_prefix_size = 10 - len(KNOWN_VALID_CEPS)
    top_prefix = random_ceps[:top_prefix_size]
    rest = random_ceps[top_prefix_size:]

    top_ten = KNOWN_VALID_CEPS + top_prefix
    random.shuffle(top_ten)

    dataset = top_ten + rest

    if len(dataset) != total:
        raise ValueError("A lista final de CEPs não possui a quantidade esperada.")

    if len(set(dataset)) != total:
        raise ValueError("A lista final de CEPs contém duplicados.")

    return dataset


def save_ceps_to_csv(ceps: list[str], output_path: Path) -> None:
    """
    Salva a lista de CEPs em CSV com uma coluna chamada 'cep'.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({"cep": ceps})
    df.to_csv(output_path, index=False)

    logger.info("Arquivo CSV gerado com sucesso em: %s", output_path)


def main() -> None:
    setup_logging("INFO")
    random.seed(RANDOM_SEED)

    logger.info("Iniciando geração de %s CEPs", TOTAL_CEPS)

    ceps = build_cep_dataset(TOTAL_CEPS)
    save_ceps_to_csv(ceps, OUTPUT_PATH)

    logger.info("Total de CEPs gerados: %s", len(ceps))
    logger.info("Top 10 CEPs gerados: %s", ceps[:10])
    logger.info("CEPs conhecidos garantidos no top 10: %s", KNOWN_VALID_CEPS)


if __name__ == "__main__":
    main()

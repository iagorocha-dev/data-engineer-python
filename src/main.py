import asyncio
import time

from src.config import Settings
from src.io.cep_reader import load_ceps
from src.viacep.async_client import fetch_all_ceps


def main() -> None:
    settings = Settings()

    valid_ceps, invalid_rows = load_ceps(str(settings.input_csv))
    sample_ceps = valid_ceps[:500]

    start = time.perf_counter()

    addresses, errors = asyncio.run(
        fetch_all_ceps(
            sample_ceps,
            base_url=settings.viacep_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            max_concurrency=settings.max_concurrency,
            max_retries=settings.max_retries,
            batch_size=50,
        )
    )

    elapsed = time.perf_counter() - start

    print(f"Total de CEPs válidos carregados: {len(valid_ceps)}")
    print(f"Total de CEPs inválidos carregados: {len(invalid_rows)}")
    print(f"Total processado na amostra: {len(sample_ceps)}")
    print(f"Sucessos: {len(addresses)}")
    print(f"Erros: {len(errors)}")
    print(f"Tempo total: {elapsed:.2f}s")

    if addresses:
        print(
            f"Exemplo de sucesso: CEP={addresses[0].cep} | "
            f"Localidade={addresses[0].localidade} | UF={addresses[0].uf}"
        )

    if errors:
        print(f"Exemplo de erro: {errors[0]}")


if __name__ == "__main__":
    main()
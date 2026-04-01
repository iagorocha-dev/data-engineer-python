import asyncio
import time

from src.config import Settings
from src.db.repository import save_addresses
from src.db.session import create_session_factory
from src.io.cep_reader import load_ceps
from src.io.exporters import export_to_json, export_to_xml
from src.io.writers import write_errors_csv
from src.utils.logging import setup_logging
from src.viacep.async_client import fetch_all_ceps


def main() -> None:
    settings = Settings()
    setup_logging(settings.log_level)

    valid_ceps, invalid_rows = load_ceps(str(settings.input_csv))
    sample_ceps = valid_ceps[:20]

    start = time.perf_counter()

    addresses, api_errors = asyncio.run(
        fetch_all_ceps(
            sample_ceps,
            base_url=settings.viacep_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            max_concurrency=settings.max_concurrency,
            max_retries=settings.max_retries,
            batch_size=settings.batch_size,
            requests_per_second=settings.requests_per_second,
            batch_pause_seconds=settings.batch_pause_seconds,
        )
    )

    elapsed = time.perf_counter() - start
    all_errors = invalid_rows + api_errors

    session_factory = create_session_factory(settings.database_url)
    with session_factory() as session:
        save_addresses(session, addresses)

    errors_output_path = settings.output_dir / "errors.csv"
    write_errors_csv(errors_output_path, all_errors)

    json_path = settings.output_dir / "addresses.json"
    xml_path = settings.output_dir / "addresses.xml"
    export_to_json(json_path, addresses)
    export_to_xml(xml_path, addresses)

    print(f"Total de CEPs válidos carregados: {len(valid_ceps)}")
    print(f"Total de CEPs inválidos carregados: {len(invalid_rows)}")
    print(f"Total processado na amostra: {len(sample_ceps)}")
    print(f"Sucessos: {len(addresses)}")
    print(f"Erros: {len(all_errors)}")
    print(f"Tempo total: {elapsed:.2f}s")
    print(f"Arquivo de erros gerado em: {errors_output_path}")
    print(f"Banco utilizado: {settings.database_url}")
    print(f"Arquivo JSON gerado em: {json_path}")
    print(f"Arquivo XML gerado em: {xml_path}")

    if addresses:
        print(
            f"Exemplo de sucesso: CEP={addresses[0].cep} | "
            f"Localidade={addresses[0].localidade} | UF={addresses[0].uf}"
        )

    if all_errors:
        print(f"Exemplo de erro: {all_errors[0]}")


if __name__ == "__main__":
    main()
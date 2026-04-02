import asyncio
import logging
import time

from src.config import Settings
from src.db.repository import save_addresses
from src.db.session import create_session_factory
from src.io.cep_reader import load_ceps
from src.io.exporters import export_to_json, export_to_xml
from src.io.writers import write_errors_csv
from src.utils.logging import setup_logging
from src.viacep.async_client import fetch_all_ceps

logger = logging.getLogger(__name__)


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

    logger.info("Total de CEPs válidos carregados: %s", len(valid_ceps))
    logger.info("Total de CEPs inválidos carregados: %s", len(invalid_rows))
    logger.info("Total processado na amostra: %s", len(sample_ceps))
    logger.info("Sucessos: %s", len(addresses))
    logger.info("Erros: %s", len(all_errors))
    logger.info("Tempo total: %.2fs", elapsed)
    logger.info("Arquivo de erros gerado em: %s", errors_output_path)
    logger.info("Banco utilizado: %s", settings.database_url)
    logger.info("Arquivo JSON gerado em: %s", json_path)
    logger.info("Arquivo XML gerado em: %s", xml_path)

    if addresses:
        logger.info(
            "Exemplo de sucesso: CEP=%s | Localidade=%s | UF=%s",
            addresses[0].cep,
            addresses[0].localidade,
            addresses[0].uf,
        )

    if all_errors:
        logger.info("Exemplo de erro: %s", all_errors[0])


if __name__ == "__main__":
    main()
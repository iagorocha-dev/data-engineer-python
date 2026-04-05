import asyncio
import logging
import time
from typing import Any

from src.config import Settings
from src.db.repository import load_all_addresses, load_processed_ceps, save_addresses
from src.db.session import create_session_factory
from src.io.cep_reader import load_ceps
from src.io.exporters import export_to_json, export_to_xml
from src.io.writers import append_errors_csv, load_error_ceps
from src.utils.logging import setup_logging
from src.viacep.async_client import fetch_all_ceps

logger = logging.getLogger(__name__)


def should_stop_due_to_probable_block(errors: list[dict[str, Any]]) -> bool:
    if not errors:
        return False

    transient_count = 0
    hard_block_count = 0

    for error in errors:
        error_type = error.get("error_type")
        status_code = str(error.get("status_code", "")).strip()

        if error_type == "timeout_or_network":
            transient_count += 1

        elif error_type == "http_retry_exceeded":
            transient_count += 1
            if status_code in {"429", "403"}:
                hard_block_count += 1

        elif error_type == "http_error":
            if status_code in {"429", "403"}:
                hard_block_count += 1
                transient_count += 1
            elif status_code.startswith("5"):
                transient_count += 1

    if hard_block_count > 0:
        return True

    if transient_count == len(errors):
        return True

    if transient_count >= max(5, int(len(errors) * 0.8)):
        return True

    return False


def main() -> None:
    settings = Settings()
    setup_logging(settings.log_level)

    valid_ceps, invalid_rows = load_ceps(str(settings.input_csv))

    session_factory = create_session_factory(settings.database_url)
    errors_output_path = settings.output_dir / "errors.csv"

    # 1) Carrega histórico de CEPs já processados
    with session_factory() as session:
        db_processed_ceps = load_processed_ceps(session)

    error_processed_ceps = load_error_ceps(errors_output_path)
    already_processed_ceps = db_processed_ceps | error_processed_ceps

    # 2) Registra erros de validação local (uma única vez)
    invalid_ceps = {
        str(row.get("cep", "")).strip()
        for row in invalid_rows
        if str(row.get("cep", "")).strip()
    }

    pending_invalid_rows = [
        row
        for row in invalid_rows
        if str(row.get("cep", "")).strip() not in error_processed_ceps
    ]

    if pending_invalid_rows:
        append_errors_csv(errors_output_path, pending_invalid_rows)

    already_processed_ceps |= invalid_ceps

    # 3) Calcula o que realmente importa para o arquivo atual
    already_processed_in_current_file = set(valid_ceps) & already_processed_ceps
    pending_ceps = [cep for cep in valid_ceps if cep not in already_processed_ceps]

    logger.info(
        "Execução iniciada | total_valid=%s | total_invalid=%s | already_processed_current=%s | pending=%s",
        len(valid_ceps),
        len(invalid_rows),
        len(already_processed_in_current_file),
        len(pending_ceps),
    )

    if not pending_ceps:
        logger.info("Nenhum CEP pendente. Gerando exportações finais.")

        with session_factory() as session:
            persisted_addresses = load_all_addresses(session)

        json_path = settings.output_dir / "addresses.json"
        xml_path = settings.output_dir / "addresses.xml"
        export_to_json(json_path, persisted_addresses)
        export_to_xml(xml_path, persisted_addresses)

        logger.info(
            "Artefatos gerados | db=%s | errors=%s | json=%s | xml=%s",
            settings.database_url,
            errors_output_path,
            json_path,
            xml_path,
        )
        return

    start = time.perf_counter()

    attempted_now = 0
    total_success = 0
    total_errors = len(pending_invalid_rows)
    total_batches = (len(pending_ceps) + settings.batch_size - 1) // settings.batch_size

    # 4) Processa incrementalmente batch a batch
    for batch_number, start_index in enumerate(
        range(0, len(pending_ceps), settings.batch_size),
        start=1,
    ):
        batch = pending_ceps[start_index : start_index + settings.batch_size]
        remaining_after_batch = max(0, len(pending_ceps) - (start_index + len(batch)))

        logger.info(
            "Batch incremental %s/%s | size=%s | remaining_after=%s",
            batch_number,
            total_batches,
            len(batch),
            remaining_after_batch,
        )

        addresses, api_errors = asyncio.run(
            fetch_all_ceps(
                batch,
                base_url=settings.viacep_base_url,
                timeout_seconds=settings.request_timeout_seconds,
                max_concurrency=settings.max_concurrency,
                max_retries=settings.max_retries,
                batch_size=settings.batch_size,
                requests_per_second=settings.requests_per_second,
                batch_pause_seconds=settings.batch_pause_seconds,
            )
        )
        probable_block = should_stop_due_to_probable_block(api_errors)

        # 5) Persiste imediatamente o que deu certo
        with session_factory() as session:
            save_addresses(session, addresses)

        attempted_now += len(batch)
        total_success += len(addresses)
        total_errors += len(api_errors)

        if probable_block:
            batch_end_index = start_index + len(batch)
            remaining_after_batch = max(0, len(pending_ceps) - batch_end_index)

            logger.warning(
                "Execução interrompida por indício de bloqueio ou indisponibilidade do ViaCEP | "
                "batch=%s/%s | remaining_after=%s | blocked_batch_errors=%s",
                batch_number,
                total_batches,
                remaining_after_batch,
                len(api_errors),
            )
            break

        # 6) Anexa imediatamente os erros do batch
        if api_errors:
            append_errors_csv(errors_output_path, api_errors)

        logger.info(
            "Batch incremental %s/%s concluído | success=%s | errors=%s | accumulated_success=%s | accumulated_errors=%s",
            batch_number,
            total_batches,
            len(addresses),
            len(api_errors),
            total_success,
            total_errors,
        )

    elapsed = time.perf_counter() - start

    # 7) Exportação final a partir do banco
    with session_factory() as session:
        persisted_addresses = load_all_addresses(session)

    json_path = settings.output_dir / "addresses.json"
    xml_path = settings.output_dir / "addresses.xml"
    export_to_json(json_path, persisted_addresses)
    export_to_xml(xml_path, persisted_addresses)

    logger.info(
        "Execução finalizada | attempted_now=%s | success_now=%s | errors_now=%s | total_time=%.2fs",
        attempted_now,
        total_success,
        total_errors,
        elapsed,
    )
    
    logger.info(
        "Artefatos gerados | db=%s | errors=%s | json=%s | xml=%s",
        settings.database_url,
        errors_output_path,
        json_path,
        xml_path,
    )

    if persisted_addresses:
        logger.info(
            "Exemplo de sucesso: CEP=%s | Localidade=%s | UF=%s",
            persisted_addresses[0].cep,
            persisted_addresses[0].localidade,
            persisted_addresses[0].uf,
        )


if __name__ == "__main__":
    main()

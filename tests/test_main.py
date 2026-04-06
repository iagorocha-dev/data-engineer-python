from pathlib import Path
from types import SimpleNamespace

from src.main import main
from src.viacep.models import Address


class DummySessionFactory:
    def __call__(self) -> "DummySessionFactory":
        return self

    def __enter__(self) -> object:
        return object()

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_main_counts_blocked_batch_without_marking_it_as_processed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import src.main as main_module

    settings = SimpleNamespace(
        input_csv=tmp_path / "input.csv",
        output_dir=tmp_path / "output",
        database_url="sqlite:///test.db",
        viacep_base_url="https://viacep.com.br/ws",
        request_timeout_seconds=5.0,
        max_concurrency=2,
        max_retries=1,
        requests_per_second=2,
        batch_pause_seconds=0.0,
        batch_size=2,
        log_level="INFO",
    )

    persisted_addresses: list[Address] = []
    exported_artifacts: list[tuple[str, str, int]] = []
    appended_errors: list[list[dict[str, object]]] = []
    info_logs: list[tuple[str, tuple[object, ...]]] = []
    warning_logs: list[tuple[str, tuple[object, ...]]] = []

    monkeypatch.setattr(main_module, "Settings", lambda: settings)
    monkeypatch.setattr(main_module, "setup_logging", lambda level: None)
    monkeypatch.setattr(
        main_module,
        "load_ceps",
        lambda _: (["01001000", "02002000", "03003000"], []),
    )
    monkeypatch.setattr(main_module, "create_session_factory", lambda _: DummySessionFactory())
    monkeypatch.setattr(main_module, "load_processed_ceps", lambda _: set())
    monkeypatch.setattr(main_module, "load_error_ceps", lambda _: set())
    monkeypatch.setattr(
        main_module,
        "save_addresses",
        lambda _, addresses: persisted_addresses.extend(addresses),
    )
    monkeypatch.setattr(
        main_module,
        "load_all_addresses",
        lambda _: list(persisted_addresses),
    )
    monkeypatch.setattr(
        main_module,
        "append_errors_csv",
        lambda _, errors: appended_errors.append(list(errors)),
    )
    monkeypatch.setattr(
        main_module,
        "export_to_json",
        lambda path, addresses: exported_artifacts.append(
            ("json", path.name, len(addresses))
        ),
    )
    monkeypatch.setattr(
        main_module,
        "export_to_xml",
        lambda path, addresses: exported_artifacts.append(
            ("xml", path.name, len(addresses))
        ),
    )
    monkeypatch.setattr(
        main_module.logger,
        "info",
        lambda message, *args: info_logs.append((message, args)),
    )
    monkeypatch.setattr(
        main_module.logger,
        "warning",
        lambda message, *args: warning_logs.append((message, args)),
    )

    async def fake_fetch_all_ceps(batch: list[str], **kwargs):
        return [
            Address(
                cep=batch[0],
                localidade="Sao Paulo",
                uf="SP",
            )
        ], [
            {
                "cep": batch[1],
                "error_type": "http_error",
                "status_code": 403,
                "message": "HTTP 403 ao consultar ViaCEP",
            }
        ]

    monkeypatch.setattr(main_module, "fetch_all_ceps", fake_fetch_all_ceps)

    main()

    assert [address.cep for address in persisted_addresses] == ["01001000"]
    assert appended_errors == []
    assert exported_artifacts == [
        ("json", "addresses.json", 1),
        ("xml", "addresses.xml", 1),
    ]
    assert len(warning_logs) == 1

    final_log_args = next(
        args
        for message, args in info_logs
        if message.startswith("Execução finalizada")
    )
    assert final_log_args[:3] == (2, 1, 1)

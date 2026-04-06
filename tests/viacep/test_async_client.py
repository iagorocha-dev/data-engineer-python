import asyncio
from typing import Any

import httpx
import pytest

from src.viacep.async_client import (
    AsyncRateLimiter,
    AsyncViaCepClient,
    calculate_backoff,
    fetch_all_ceps,
)


class FakeAsyncResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeAsyncClient:
    def __init__(self, responses: list[Any]):
        self._responses = responses
        self._index = 0

    async def get(self, url: str, timeout: float):
        response = self._responses[self._index]
        self._index += 1

        if isinstance(response, Exception):
            raise response

        return response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_async_fetch_returns_not_found_for_viacep_error_string() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=2,
    )

    fake_http_client = FakeAsyncClient(
        [FakeAsyncResponse(200, {"erro": "true"})]
    )

    address, error = await client.fetch(fake_http_client, "88888888")

    assert address is None
    assert error is not None
    assert error["error_type"] == "not_found"


@pytest.mark.asyncio
async def test_async_fetch_returns_address_on_success() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=2,
    )

    fake_http_client = FakeAsyncClient(
        [
            FakeAsyncResponse(
                200,
                {
                    "cep": "01310-100",
                    "logradouro": "Avenida Paulista",
                    "bairro": "Bela Vista",
                    "localidade": "São Paulo",
                    "uf": "SP",
                    "ibge": "3550308",
                    "gia": "1004",
                    "ddd": "11",
                    "siafi": "7107",
                },
            )
        ]
    )

    address, error = await client.fetch(fake_http_client, "01310100")

    assert error is None
    assert address is not None
    assert address.cep == "01310100"
    assert address.localidade == "São Paulo"
    assert address.uf == "SP"


@pytest.mark.asyncio
async def test_async_fetch_retries_on_transient_http_status() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=2,
    )

    fake_http_client = FakeAsyncClient(
        [
            FakeAsyncResponse(503, {}),
            FakeAsyncResponse(
                200,
                {
                    "cep": "01310-100",
                    "logradouro": "Avenida Paulista",
                    "bairro": "Bela Vista",
                    "localidade": "São Paulo",
                    "uf": "SP",
                },
            ),
        ]
    )

    address, error = await client.fetch(fake_http_client, "01310100")

    assert error is None
    assert address is not None
    assert address.cep == "01310100"


@pytest.mark.asyncio
async def test_async_fetch_retries_on_timeout_and_returns_error_when_exhausted() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=1,
    )

    fake_http_client = FakeAsyncClient(
        [
            httpx.TimeoutException("timeout"),
            httpx.TimeoutException("timeout again"),
        ]
    )

    address, error = await client.fetch(fake_http_client, "01310100")

    assert address is None
    assert error is not None
    assert error["error_type"] == "timeout_or_network"


@pytest.mark.asyncio
async def test_fetch_all_ceps_returns_addresses_and_errors(monkeypatch) -> None:
    responses = [
        FakeAsyncResponse(
            200,
            {
                "cep": "01310-100",
                "logradouro": "Avenida Paulista",
                "bairro": "Bela Vista",
                "localidade": "São Paulo",
                "uf": "SP",
            },
        ),
        FakeAsyncResponse(200, {"erro": "true"}),
    ]

    fake_client = FakeAsyncClient(responses)

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda: fake_client,
    )

    addresses, errors = await fetch_all_ceps(
        ["01310100", "88888888"],
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_concurrency=2,
        max_retries=1,
        batch_size=2,
        requests_per_second=10,
        batch_pause_seconds=0,
    )

    assert len(addresses) == 1
    assert len(errors) == 1
    assert addresses[0].cep == "01310100"
    assert errors[0]["error_type"] == "not_found"


def test_calculate_backoff_grows_exponentially() -> None:
    assert calculate_backoff(0) == 0.3
    assert calculate_backoff(2) == 1.2


@pytest.mark.asyncio
async def test_rate_limiter_waits_when_limit_is_reached() -> None:
    limiter = AsyncRateLimiter(max_calls=1, period_seconds=0.01)
    await limiter.acquire()
    await limiter.acquire()
    assert len(limiter.calls) == 1


@pytest.mark.asyncio
async def test_rate_limiter_discards_expired_calls_from_window() -> None:
    limiter = AsyncRateLimiter(max_calls=1, period_seconds=0.01)

    await limiter.acquire()

    await asyncio.sleep(0.02)
    await limiter.acquire()

    assert len(limiter.calls) == 1


@pytest.mark.asyncio
async def test_async_fetch_returns_retry_exceeded_after_transient_http_failures() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=1,
    )

    fake_http_client = FakeAsyncClient(
        [
            FakeAsyncResponse(503, {}),
            FakeAsyncResponse(503, {}),
        ]
    )

    address, error = await client.fetch(fake_http_client, "01310100")

    assert address is None
    assert error is not None
    assert error["error_type"] == "http_retry_exceeded"
    assert error["status_code"] == 503


@pytest.mark.asyncio
async def test_async_fetch_returns_http_error_for_non_200_non_retryable_status() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=1,
    )

    address, error = await client.fetch(
        FakeAsyncClient([FakeAsyncResponse(404, {})]),
        "01310100",
    )

    assert address is None
    assert error is not None
    assert error["error_type"] == "http_error"
    assert error["status_code"] == 404


@pytest.mark.asyncio
async def test_async_fetch_returns_parse_error_when_json_is_invalid() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=1,
    )

    class InvalidJsonResponse:
        status_code = 200

        def json(self) -> dict[str, Any]:
            raise ValueError("invalid json")

    address, error = await client.fetch(
        FakeAsyncClient([InvalidJsonResponse()]),
        "01310100",
    )

    assert address is None
    assert error is not None
    assert error["error_type"] == "parse_error"


@pytest.mark.asyncio
async def test_async_fetch_returns_unexpected_error_for_unknown_exception() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=1,
    )

    address, error = await client.fetch(
        FakeAsyncClient([RuntimeError("boom")]),
        "01310100",
    )

    assert address is None
    assert error is not None
    assert error["error_type"] == "unexpected_error"
    assert "boom" in error["message"]


@pytest.mark.asyncio
async def test_async_fetch_returns_fallback_unexpected_error_when_loop_does_not_run() -> None:
    client = AsyncViaCepClient(
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_retries=-1,
    )

    address, error = await client.fetch(FakeAsyncClient([]), "01310100")

    assert address is None
    assert error is not None
    assert error["error_type"] == "unexpected_error"
    assert error["message"] == "Falha não mapeada durante a consulta"


@pytest.mark.asyncio
async def test_fetch_all_ceps_waits_between_batches(monkeypatch) -> None:
    responses = [
        FakeAsyncResponse(200, {"cep": "01310-100", "localidade": "São Paulo", "uf": "SP"}),
        FakeAsyncResponse(200, {"erro": "true"}),
    ]
    fake_client = FakeAsyncClient(responses)
    slept: list[float] = []

    async def fake_sleep(duration: float) -> None:
        slept.append(duration)

    monkeypatch.setattr(httpx, "AsyncClient", lambda: fake_client)
    monkeypatch.setattr("src.viacep.async_client.asyncio.sleep", fake_sleep)

    addresses, errors = await fetch_all_ceps(
        ["01310100", "88888888"],
        base_url="https://viacep.com.br/ws",
        timeout_seconds=5.0,
        max_concurrency=1,
        max_retries=0,
        batch_size=1,
        requests_per_second=10,
        batch_pause_seconds=0.25,
    )

    assert len(addresses) == 1
    assert len(errors) == 1
    assert slept == [0.25]

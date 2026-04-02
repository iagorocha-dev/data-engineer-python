from typing import Any

import httpx

from src.viacep.client import ViaCepClient


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeClient:
    def __init__(self, response: FakeResponse):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def get(self, url: str) -> FakeResponse:
        return self.response


def test_fetch_returns_address_on_success(monkeypatch) -> None:
    response = FakeResponse(
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

    monkeypatch.setattr(httpx, "Client", lambda timeout: FakeClient(response))

    client = ViaCepClient("https://viacep.com.br/ws", 5.0)
    address, error = client.fetch("01310100")

    assert error is None
    assert address is not None
    assert address.cep == "01310100"
    assert address.localidade == "São Paulo"
    assert address.uf == "SP"


def test_fetch_returns_not_found_error_when_viacep_returns_erro_true_string(monkeypatch) -> None:
    response = FakeResponse(200, {"erro": "true"})

    monkeypatch.setattr(httpx, "Client", lambda timeout: FakeClient(response))

    client = ViaCepClient("https://viacep.com.br/ws", 5.0)
    address, error = client.fetch("88888888")

    assert address is None
    assert error is not None
    assert error["error_type"] == "not_found"


def test_fetch_returns_http_error_on_non_200_response(monkeypatch) -> None:
    response = FakeResponse(500, {})

    monkeypatch.setattr(httpx, "Client", lambda timeout: FakeClient(response))

    client = ViaCepClient("https://viacep.com.br/ws", 5.0)
    address, error = client.fetch("01310100")

    assert address is None
    assert error is not None
    assert error["error_type"] == "http_error"
    assert error["status_code"] == 500
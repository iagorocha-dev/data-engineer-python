from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.viacep.models import Address


class AsyncViaCepClient:
    """
    Client assíncrono para consultas ao ViaCEP.
    """

    def __init__(self, base_url: str, timeout_seconds: float, max_retries: int):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def fetch(
        self,
        client: httpx.AsyncClient,
        cep: str,
    ) -> tuple[Address | None, dict[str, Any] | None]:
        url = f"{self.base_url}/{cep}/json/"

        try:
            response = await client.get(url, timeout=self.timeout_seconds)

            if response.status_code != 200:
                return None, {
                    "cep": cep,
                    "error_type": "http_error",
                    "status_code": response.status_code,
                    "message": f"HTTP {response.status_code} ao consultar ViaCEP",
                }

            data = response.json()

            if data.get("erro") is True:
                return None, {
                    "cep": cep,
                    "error_type": "not_found",
                    "status_code": 200,
                    "message": "CEP não encontrado (ViaCEP retornou erro=true)",
                }

            normalized_cep = str(data.get("cep", cep)).replace("-", "")

            address = Address(
                cep=normalized_cep,
                logradouro=data.get("logradouro"),
                complemento=data.get("complemento"),
                unidade=data.get("unidade"),
                bairro=data.get("bairro"),
                localidade=data.get("localidade"),
                uf=data.get("uf"),
                ibge=data.get("ibge"),
                gia=data.get("gia"),
                ddd=data.get("ddd"),
                siafi=data.get("siafi"),
                raw=data,
            )

            return address, None

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            return None, {
                "cep": cep,
                "error_type": "timeout_or_network",
                "status_code": "",
                "message": str(exc),
            }

        except ValueError as exc:
            return None, {
                "cep": cep,
                "error_type": "parse_error",
                "status_code": 200,
                "message": f"Falha ao interpretar JSON da resposta: {exc}",
            }

        except Exception as exc:
            return None, {
                "cep": cep,
                "error_type": "unexpected_error",
                "status_code": "",
                "message": f"Erro inesperado: {exc}",
            }


async def fetch_all_ceps(
    ceps: list[str],
    *,
    base_url: str,
    timeout_seconds: float,
    max_concurrency: int,
    max_retries: int,
    batch_size: int = 200,
) -> tuple[list[Address], list[dict[str, Any]]]:
    """
    Processa CEPs em paralelo de forma controlada.
    """

    semaphore = asyncio.Semaphore(max_concurrency)
    via_cep_client = AsyncViaCepClient(
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )

    addresses: list[Address] = []
    errors: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as http_client:

        async def worker(cep: str) -> tuple[Address | None, dict[str, Any] | None]:
            async with semaphore:
                return await via_cep_client.fetch(http_client, cep)

        for start in range(0, len(ceps), batch_size):
            batch = ceps[start : start + batch_size]

            results = await asyncio.gather(*(worker(cep) for cep in batch))

            for address, error in results:
                if address is not None:
                    addresses.append(address)
                if error is not None:
                    errors.append(error)

    return addresses, errors
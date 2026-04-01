from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any

import httpx

from src.viacep.models import Address
from src.viacep.utils import is_viacep_not_found

logger = logging.getLogger(__name__)


def calculate_backoff(attempt: int) -> float:
    """
    Calcula o tempo de espera entre tentativas.
    Estratégia simples de backoff exponencial.
    """
    return 0.3 * (2 ** attempt)


class AsyncRateLimiter:
    """
    Rate limiter simples por janela deslizante.

    Exemplo:
    - max_calls=3
    - period_seconds=1.0

    Garante no máximo 3 liberações por segundo.
    """

    def __init__(self, max_calls: int, period_seconds: float = 1.0):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()

            while self.calls and now - self.calls[0] >= self.period_seconds:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                sleep_for = self.period_seconds - (now - self.calls[0])

                if sleep_for > 0:
                    logger.debug(
                        "Rate limit atingido; aguardando %.3fs | window_calls=%s/%s",
                        sleep_for,
                        len(self.calls),
                        self.max_calls,
                    )
                    await asyncio.sleep(sleep_for)

                now = time.monotonic()
                while self.calls and now - self.calls[0] >= self.period_seconds:
                    self.calls.popleft()

            self.calls.append(time.monotonic())

            logger.debug(
                "Rate limit liberado | window_calls=%s/%s",
                len(self.calls),
                self.max_calls,
            )


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

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(url, timeout=self.timeout_seconds)

                if response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        backoff = calculate_backoff(attempt)
                        logger.warning(
                            "Retry por status HTTP | cep=%s | status=%s | tentativa=%s/%s | sleep=%.2fs",
                            cep,
                            response.status_code,
                            attempt + 1,
                            self.max_retries,
                            backoff,
                        )
                        await asyncio.sleep(backoff)
                        continue

                    return None, {
                        "cep": cep,
                        "error_type": "http_retry_exceeded",
                        "status_code": response.status_code,
                        "message": f"HTTP {response.status_code} após esgotar tentativas",
                    }

                if response.status_code != 200:
                    return None, {
                        "cep": cep,
                        "error_type": "http_error",
                        "status_code": response.status_code,
                        "message": f"HTTP {response.status_code} ao consultar ViaCEP",
                    }

                data = response.json()

                if is_viacep_not_found(data):
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
                if attempt < self.max_retries:
                    backoff = calculate_backoff(attempt)
                    logger.warning(
                        "Retry por timeout/rede | cep=%s | tentativa=%s/%s | sleep=%.2fs | detalhe=%s",
                        cep,
                        attempt + 1,
                        self.max_retries,
                        backoff,
                        exc,
                    )
                    await asyncio.sleep(backoff)
                    continue

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

        return None, {
            "cep": cep,
            "error_type": "unexpected_error",
            "status_code": "",
            "message": "Falha não mapeada durante a consulta",
        }


async def fetch_all_ceps(
    ceps: list[str],
    *,
    base_url: str,
    timeout_seconds: float,
    max_concurrency: int,
    max_retries: int,
    batch_size: int = 5,
    requests_per_second: int = 3,
    batch_pause_seconds: float = 1.0,
) -> tuple[list[Address], list[dict[str, Any]]]:
    """
    Processa CEPs em paralelo de forma controlada.

    Controles aplicados:
    - concorrência máxima (semaphore)
    - taxa máxima por segundo (rate limiter)
    - pausa entre batches
    """

    semaphore = asyncio.Semaphore(max_concurrency)
    rate_limiter = AsyncRateLimiter(
        max_calls=requests_per_second,
        period_seconds=1.0,
    )

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
                await rate_limiter.acquire()
                logger.debug("Disparando requisição | cep=%s", cep)
                return await via_cep_client.fetch(http_client, cep)

        total_batches = (len(ceps) + batch_size - 1) // batch_size

        for batch_index, start in enumerate(range(0, len(ceps), batch_size), start=1):
            batch = ceps[start : start + batch_size]

            logger.info(
                "Iniciando batch %s/%s | size=%s",
                batch_index,
                total_batches,
                len(batch),
            )

            results = await asyncio.gather(*(worker(cep) for cep in batch))

            batch_success = 0
            batch_errors = 0

            for address, error in results:
                if address is not None:
                    addresses.append(address)
                    batch_success += 1
                if error is not None:
                    errors.append(error)
                    batch_errors += 1

            logger.info(
                "Finalizando batch %s/%s | success=%s | errors=%s",
                batch_index,
                total_batches,
                batch_success,
                batch_errors,
            )

            if batch_index < total_batches:
                logger.debug(
                    "Pausa entre batches | sleep=%.2fs",
                    batch_pause_seconds,
                )
                await asyncio.sleep(batch_pause_seconds)

    return addresses, errors
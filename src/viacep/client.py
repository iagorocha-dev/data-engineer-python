from __future__ import annotations

from typing import Any

import httpx

from src.viacep.models import Address
from src.viacep.utils import is_viacep_not_found


class ViaCepClient:
    """
    Client síncrono para consultas ao ViaCEP.

    Retorno padronizado:
    - sucesso -> (Address, None)
    - erro    -> (None, error_dict)
    """

    def __init__(self, base_url: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def fetch(self, cep: str) -> tuple[Address | None, dict[str, Any] | None]:
        url = f"{self.base_url}/{cep}/json/"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url)

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

        except httpx.TimeoutException as exc:
            return None, {
                "cep": cep,
                "error_type": "timeout",
                "status_code": "",
                "message": f"Timeout ao consultar ViaCEP: {exc}",
            }

        except httpx.NetworkError as exc:
            return None, {
                "cep": cep,
                "error_type": "network_error",
                "status_code": "",
                "message": f"Erro de rede ao consultar ViaCEP: {exc}",
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
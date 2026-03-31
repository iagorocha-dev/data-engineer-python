from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Address:
    cep: str
    logradouro: str | None = None
    complemento: str | None = None
    unidade: str | None = None
    bairro: str | None = None
    localidade: str | None = None
    uf: str | None = None
    ibge: str | None = None
    gia: str | None = None
    ddd: str | None = None
    siafi: str | None = None
    raw: dict[str, Any] | None = None
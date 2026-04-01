from __future__ import annotations

from sqlalchemy.orm import Session

from src.db.models import AddressRecord
from src.viacep.models import Address


def save_addresses(session: Session, addresses: list[Address]) -> None:
    """
    Persiste endereços no banco.

    Usa session.merge para garantir idempotência baseada no CEP.
    """
    for address in addresses:
        record = AddressRecord(
            cep=address.cep,
            logradouro=address.logradouro,
            complemento=address.complemento,
            unidade=address.unidade,
            bairro=address.bairro,
            localidade=address.localidade,
            uf=address.uf,
            ibge=address.ibge,
            gia=address.gia,
            ddd=address.ddd,
            siafi=address.siafi,
        )
        session.merge(record)

    session.commit()
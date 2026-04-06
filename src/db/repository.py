from __future__ import annotations

from sqlalchemy import select
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


def load_processed_ceps(session: Session) -> set[str]:
    """
    Retorna todos os CEPs já persistidos no banco.
    """
    result = session.execute(select(AddressRecord.cep))
    return {row[0] for row in result.fetchall()}


def load_all_addresses(session: Session) -> list[Address]:
    """
    Carrega todos os endereços persistidos no banco.
    """
    result = session.execute(select(AddressRecord))
    records = result.scalars().all()

    return [
        Address(
            cep=record.cep,
            logradouro=record.logradouro,
            complemento=record.complemento,
            unidade=record.unidade,
            bairro=record.bairro,
            localidade=record.localidade,
            uf=record.uf,
            ibge=record.ibge,
            gia=record.gia,
            ddd=record.ddd,
            siafi=record.siafi,
        )
        for record in records
    ]
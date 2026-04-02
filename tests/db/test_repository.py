from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.repository import save_addresses
from src.viacep.models import Address


def test_save_addresses_persists_records() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    addresses = [
        Address(
            cep="01310100",
            logradouro="Avenida Paulista",
            bairro="Bela Vista",
            localidade="São Paulo",
            uf="SP",
            ibge="3550308",
            gia=None,
            ddd="11",
            siafi="7107",
        )
    ]

    with SessionLocal() as session:
        save_addresses(session, addresses)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM addresses"))
        count = result.scalar_one()

    assert count == 1


def test_save_addresses_is_idempotent_by_cep() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    address = Address(
        cep="01310100",
        logradouro="Avenida Paulista",
        bairro="Bela Vista",
        localidade="São Paulo",
        uf="SP",
        ibge="3550308",
        gia=None,
        ddd="11",
        siafi="7107",
    )

    with SessionLocal() as session:
        save_addresses(session, [address])
        save_addresses(session, [address])

    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM addresses"))
        count = result.scalar_one()

    assert count == 1
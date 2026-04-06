from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.repository import load_all_addresses, load_processed_ceps, save_addresses
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


def test_load_processed_ceps_returns_all_persisted_ceps() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    addresses = [
        Address(cep="01310100", localidade="São Paulo", uf="SP"),
        Address(cep="01001000", localidade="São Paulo", uf="SP"),
    ]

    with SessionLocal() as session:
        save_addresses(session, addresses)

        assert load_processed_ceps(session) == {"01310100", "01001000"}


def test_load_all_addresses_maps_records_back_to_domain_objects() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    address = Address(
        cep="01310100",
        logradouro="Avenida Paulista",
        complemento="Conjunto 101",
        unidade="A",
        bairro="Bela Vista",
        localidade="São Paulo",
        uf="SP",
        ibge="3550308",
        gia="1004",
        ddd="11",
        siafi="7107",
    )

    with SessionLocal() as session:
        save_addresses(session, [address])
        loaded = load_all_addresses(session)

    assert len(loaded) == 1
    assert loaded[0].cep == address.cep
    assert loaded[0].logradouro == address.logradouro
    assert loaded[0].complemento == address.complemento
    assert loaded[0].unidade == address.unidade
    assert loaded[0].bairro == address.bairro
    assert loaded[0].localidade == address.localidade
    assert loaded[0].uf == address.uf
    assert loaded[0].ibge == address.ibge
    assert loaded[0].gia == address.gia
    assert loaded[0].ddd == address.ddd
    assert loaded[0].siafi == address.siafi

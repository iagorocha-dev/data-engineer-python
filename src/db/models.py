from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AddressRecord(Base):
    __tablename__ = "addresses"

    cep: Mapped[str] = mapped_column(String(8), primary_key=True)
    logradouro: Mapped[str | None] = mapped_column(String, nullable=True)
    complemento: Mapped[str | None] = mapped_column(String, nullable=True)
    unidade: Mapped[str | None] = mapped_column(String, nullable=True)
    bairro: Mapped[str | None] = mapped_column(String, nullable=True)
    localidade: Mapped[str | None] = mapped_column(String, nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    ibge: Mapped[str | None] = mapped_column(String, nullable=True)
    gia: Mapped[str | None] = mapped_column(String, nullable=True)
    ddd: Mapped[str | None] = mapped_column(String, nullable=True)
    siafi: Mapped[str | None] = mapped_column(String, nullable=True)
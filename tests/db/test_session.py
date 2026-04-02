from pathlib import Path

from src.db.session import create_session_factory


def test_create_session_factory_creates_sqlite_database_file(tmp_path: Path) -> None:
    db_file = tmp_path / "test.db"
    database_url = f"sqlite:///{db_file}"

    session_factory = create_session_factory(database_url)

    assert session_factory is not None
    assert db_file.exists()
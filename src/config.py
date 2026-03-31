from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configurações da aplicação."""

    input_csv: Path = Path(os.getenv("INPUT_CSV", "data/input/ceps.csv"))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "data/output"))

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///data/output/ceps.db",
    )

    viacep_base_url: str = os.getenv(
        "VIACEP_BASE_URL",
        "https://viacep.com.br/ws",
    )

    request_timeout_seconds: float = float(
        os.getenv("REQUEST_TIMEOUT_SECONDS", "8")
    )

    max_concurrency: int = int(
        os.getenv("MAX_CONCURRENCY", "20")
    )

    max_retries: int = int(
        os.getenv("MAX_RETRIES", "2")
    )
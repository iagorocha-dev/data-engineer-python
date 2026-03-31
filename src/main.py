from src.config import Settings
from src.io.cep_reader import load_ceps


def main() -> None:
    settings = Settings()

    valid_ceps, invalid_rows = load_ceps(str(settings.input_csv))

    print(f"Total de CEPs válidos: {len(valid_ceps)}")
    print(f"Total de CEPs inválidos: {len(invalid_rows)}")
    print(f"Amostra de CEPs válidos: {valid_ceps[:5]}")
    print(f"Amostra de erros: {invalid_rows[:2]}")


if __name__ == "__main__":
    main()
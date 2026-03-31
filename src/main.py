from src.config import Settings
from src.io.cep_reader import load_ceps
from src.viacep.client import ViaCepClient


def main() -> None:
    settings = Settings()

    valid_ceps, invalid_rows = load_ceps(str(settings.input_csv))

    client = ViaCepClient(
        base_url=settings.viacep_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )

    sample_ceps = valid_ceps[:5]

    print(f"Total de CEPs válidos carregados: {len(valid_ceps)}")
    print(f"Total de CEPs inválidos carregados: {len(invalid_rows)}")
    print(f"Testando amostra: {sample_ceps}")

    for cep in sample_ceps:
        address, error = client.fetch(cep)

        if address:
            print(
                f"[OK] CEP={address.cep} | "
                f"Localidade={address.localidade} | UF={address.uf}"
            )
        else:
            print(f"[ERRO] {error}")


if __name__ == "__main__":
    main()
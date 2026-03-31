from typing import Any


def is_viacep_not_found(data: dict[str, Any]) -> bool:
    """
    Identifica resposta de CEP não encontrado no ViaCEP.

    O ViaCEP pode retornar:
    - {"erro": True}
    - {"erro": "true"}

    Essa função garante robustez contra variações de tipo.
    """
    erro = data.get("erro")

    if isinstance(erro, bool):
        return erro

    if isinstance(erro, str):
        return erro.strip().lower() == "true"

    return False
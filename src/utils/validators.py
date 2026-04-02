import re

_NON_DIGITS = re.compile(r"\D+")


def normalize_cep(value: str) -> str:
    """
    Normaliza o CEP:
    - remove caracteres não numéricos
    - remove espaços
    - completa com zeros à esquerda até 8 dígitos
    - se não houver nenhum dígito, retorna string vazia
    """
    if value is None:
        return ""

    value_str = str(value).strip()
    digits_only = _NON_DIGITS.sub("", value_str)

    if not digits_only:
        return ""

    return digits_only.zfill(8)


def is_valid_cep(cep: str) -> bool:
    """
    Considera válido apenas CEP com exatamente 8 dígitos numéricos.
    """
    return bool(re.fullmatch(r"\d{8}", cep))
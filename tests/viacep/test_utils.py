from src.viacep.utils import is_viacep_not_found


def test_is_viacep_not_found_with_boolean_true() -> None:
    assert is_viacep_not_found({"erro": True}) is True


def test_is_viacep_not_found_with_string_true() -> None:
    assert is_viacep_not_found({"erro": "true"}) is True


def test_is_viacep_not_found_with_string_true_uppercase() -> None:
    assert is_viacep_not_found({"erro": "TRUE"}) is True


def test_is_viacep_not_found_with_false_value() -> None:
    assert is_viacep_not_found({"erro": False}) is False


def test_is_viacep_not_found_with_missing_key() -> None:
    assert is_viacep_not_found({}) is False
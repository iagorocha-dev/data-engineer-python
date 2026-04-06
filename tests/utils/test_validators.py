from src.utils.validators import normalize_cep, is_valid_cep


def test_normalize_cep_removes_non_digits() -> None:
    assert normalize_cep("01.310-100") == "01310100"


def test_normalize_cep_preserves_leading_zeroes() -> None:
    assert normalize_cep("08949617") == "08949617"


def test_normalize_cep_left_pads_when_needed() -> None:
    assert normalize_cep("474177") == "00474177"


def test_normalize_cep_returns_empty_string_for_none() -> None:
    assert normalize_cep(None) == ""


def test_is_valid_cep_returns_true_for_eight_digits() -> None:
    assert is_valid_cep("01310100") is True


def test_is_valid_cep_returns_false_for_invalid_length() -> None:
    assert is_valid_cep("1310100") is False


def test_is_valid_cep_returns_false_for_non_numeric_value() -> None:
    assert is_valid_cep("ABC12345") is False

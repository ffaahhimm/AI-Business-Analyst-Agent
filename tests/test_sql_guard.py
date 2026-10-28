import pytest

from app.sql_guard import SQLValidationError, validate_sql


def test_select_is_limited():
    assert validate_sql("SELECT * FROM products").endswith("LIMIT 500")


@pytest.mark.parametrize("sql", ["DELETE FROM orders", "SELECT * FROM secrets", "SELECT 1; SELECT 2", "SELECT * FROM products -- nope"])
def test_unsafe_sql_is_rejected(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_row_limit_cannot_be_raised():
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT * FROM products", max_rows=501)


def test_existing_limit_is_preserved():
    assert validate_sql("SELECT * FROM products LIMIT 2").endswith("LIMIT 2")

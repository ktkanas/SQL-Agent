from sql_agent.safety import clean_sql, validate_sql


def test_clean_sql_translates_limit_to_top():
    assert clean_sql("SELECT name FROM customers LIMIT 10") == (
        "SELECT TOP 10 name FROM customers"
    )


def test_validate_sql_accepts_select():
    assert validate_sql("SELECT TOP 5 * FROM customers") == (True, "")


def test_validate_sql_rejects_delete():
    is_valid, error = validate_sql("DELETE FROM customers")
    assert not is_valid
    assert "DELETE" in error

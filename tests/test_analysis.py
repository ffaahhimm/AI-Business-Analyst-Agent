from app.analysis import percent_change, return_summary


def test_percent_change():
    assert percent_change(120, 100) == 20


def test_return_summary_is_ranked():
    rows = [{"label": "A", "sold": 10, "returned": 1}, {"label": "B", "sold": 10, "returned": 4}]
    assert return_summary(rows)[0]["label"] == "B"
    assert return_summary(rows)[0]["return_rate"] == 40


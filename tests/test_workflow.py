from app.seed import seed
from app.workflow import analyze


def setup_module():
    seed()


def test_revenue_has_evidence_and_trace():
    response = analyze("Why did revenue change?")
    assert response.evidence
    assert response.trace[-1].name == "assemble_report"
    assert "$" in response.summary


def test_unsupported_question_fails_safely():
    try:
        analyze("List our employees")
    except ValueError as exc:
        assert "revenue" in str(exc)
    else:
        raise AssertionError("unsupported question should fail")


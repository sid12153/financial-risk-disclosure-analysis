from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_answer_requires_citations_when_not_refused():
    payload = {
        "question": "What liquidity risks and funding sources are discussed?",
        "doc_id": "GoldmanSachs_2023_10K",
        "top_k": 5
    }
    r = client.post("/ask", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Only enforce when it answered
    if data.get("refused") is False:
        assert "citations" in data
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0

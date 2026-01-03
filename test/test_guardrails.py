from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_stock_price_prediction_is_refused():
    resp = client.post(
        "/ask",
        json={
            "question": "What will the stock price be next year?",
            "doc_id": "GoldmanSachs_2023_10K",
            "top_k": 5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is True
    assert "out-of-scope" in (data.get("refusal_reason") or "").lower() or "out-of-scope" in (data.get("answer") or "").lower()

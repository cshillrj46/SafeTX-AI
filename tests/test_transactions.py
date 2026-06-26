# File: tests/test_transactions.py


def test_analyze_high_amount_is_high_risk(client, auth_headers):
    resp = client.post(
        "/analyze",
        json={"sender": "0xabc", "recipient": "0xdef", "amount_eth": 100},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == "high-risk"


def test_analyze_without_token_is_rejected(client):
    resp = client.post(
        "/analyze",
        json={"sender": "0xabc", "recipient": "0xdef", "amount_eth": 100},
    )
    assert resp.status_code == 401


def test_history_pagination(client, auth_headers):
    for i in range(15):
        client.post(
            "/analyze",
            json={"sender": f"0x{i}", "recipient": "0xdef", "amount_eth": 1},
            headers=auth_headers,
        )

    resp = client.get("/history", params={"page": 1, "limit": 10}, headers=auth_headers)
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["items"]) == 10
    assert body["total"] == 15
    assert body["total_pages"] == 2

    resp_page_2 = client.get("/history", params={"page": 2, "limit": 10}, headers=auth_headers)
    assert len(resp_page_2.json()["items"]) == 5


def test_reclassify_uses_authenticated_user(client, auth_headers):
    client.post(
        "/analyze",
        json={"sender": "0xabc", "recipient": "0xdef", "amount_eth": 1},
        headers=auth_headers,
    )
    resp = client.patch(
        "/reclassify/1",
        json={"new_risk": "high-risk", "reason": "teste manual"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    logs = client.get("/reclassifications", headers=auth_headers).json()
    assert logs[0]["reclassified_by"] == "alice"
    assert logs[0]["reason"] == "teste manual"

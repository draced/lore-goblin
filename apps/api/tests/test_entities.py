def test_post_entity(client, campaign) -> None:
    response = client.post(
        f"/campaigns/{campaign['id']}/entities",
        json={
            "entity_type": "NPC",
            "name": "Father Aldren",
            "aliases": ["Aldren", "Priest Aldren"],
            "summary": "Chapel priest",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["entity_type"] == "NPC"
    assert body["name"] == "Father Aldren"
    assert body["summary"] == "Chapel priest"

    listed = client.get(
        f"/campaigns/{campaign['id']}/entities",
        params={"entity_type": "NPC"},
    )
    assert listed.status_code == 200
    entities = listed.json()
    assert len(entities) == 1
    assert entities[0]["name"] == "Father Aldren"


def test_invalid_entity_type_returns_400(client, campaign) -> None:
    response = client.post(
        f"/campaigns/{campaign['id']}/entities",
        json={
            "entity_type": "INVALID",
            "name": "Bad Entity",
            "summary": "Should fail",
        },
    )
    assert response.status_code == 400
    assert "Invalid entity type" in response.json()["detail"]

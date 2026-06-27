def test_player_characters_response_shape(client, campaign) -> None:
    create = client.post(
        "/player-characters",
        json={
            "campaign_id": campaign["id"],
            "name": "Nyra",
            "notes": "Half-elf ranger",
        },
    )
    assert create.status_code == 201
    created = create.json()
    assert set(created.keys()) == {
        "id",
        "campaign_id",
        "name",
        "notes",
        "created_at",
        "updated_at",
    }

    listed = client.get(f"/campaigns/{campaign['id']}/player-characters")
    assert listed.status_code == 200
    roster = listed.json()
    assert len(roster) == 1
    assert roster[0]["id"] == created["id"]
    assert roster[0]["name"] == "Nyra"
    assert roster[0]["notes"] == "Half-elf ranger"


def test_post_player_character_creates_entity_and_source(client, campaign) -> None:
    response = client.post(
        "/player-characters",
        json={
            "campaign_id": campaign["id"],
            "name": "Nyra",
            "notes": "Half-elf ranger searching for the ash crown.",
        },
    )
    assert response.status_code == 201
    character_id = response.json()["id"]

    entities = client.get(
        f"/campaigns/{campaign['id']}/entities",
        params={"entity_type": "PC"},
    )
    sources = client.get(
        f"/campaigns/{campaign['id']}/sources",
        params={"source_type": "PLAYER_CHARACTER_DESC"},
    )

    assert entities.status_code == 200
    assert sources.status_code == 200
    assert len(entities.json()) == 1
    assert entities.json()[0]["id"] == character_id
    assert entities.json()[0]["summary"] == "Half-elf ranger searching for the ash crown."
    assert len(sources.json()) == 1
    assert sources.json()[0]["entity_id"] == character_id

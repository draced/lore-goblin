def test_post_session_creates_source(client, campaign) -> None:
    response = client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-27",
            "label": "Chapel",
            "raw_content": "The party found a silver key in the ruined chapel.",
            "author_display_name": "Player One",
        },
    )
    assert response.status_code == 201

    sources = client.get(
        f"/campaigns/{campaign['id']}/sources",
        params={"source_type": "SESSION_NOTE"},
    )
    assert sources.status_code == 200
    body = sources.json()
    assert len(body) == 1
    assert body[0]["source_type"] == "SESSION_NOTE"
    assert body[0]["body"] == "The party found a silver key in the ruined chapel."
    assert body[0]["session_id"] is not None
    assert body[0]["author_user_id"] is not None


def test_source_list_filter_by_type(client, campaign) -> None:
    client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-27",
            "label": "Chapel",
            "raw_content": "Session note content.",
            "author_display_name": "Player One",
        },
    )
    client.post(
        "/player-characters",
        json={
            "campaign_id": campaign["id"],
            "name": "Nyra",
            "notes": "Half-elf ranger",
        },
    )

    session_sources = client.get(
        f"/campaigns/{campaign['id']}/sources",
        params={"source_type": "SESSION_NOTE"},
    )
    pc_sources = client.get(
        f"/campaigns/{campaign['id']}/sources",
        params={"source_type": "PLAYER_CHARACTER_DESC"},
    )

    assert session_sources.status_code == 200
    assert pc_sources.status_code == 200
    assert len(session_sources.json()) == 1
    assert len(pc_sources.json()) == 1
    assert session_sources.json()[0]["source_type"] == "SESSION_NOTE"
    assert pc_sources.json()[0]["source_type"] == "PLAYER_CHARACTER_DESC"

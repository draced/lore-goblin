from unittest.mock import patch

from lore_goblin.ollama import OllamaClient


class MockOllamaClient(OllamaClient):
    def __init__(self, answer: str = "Answer from hybrid retrieval.") -> None:
        super().__init__("http://mock", "mock")
        self.answer = answer

    def chat(self, messages, temperature=0.2, timeout=300) -> str:
        return self.answer


def test_discord_guild_ask_uses_hybrid_path(client, campaign) -> None:
    client.post("/discord/guild-links", json={"campaign_id": campaign["id"], "guild_id": "guild_test"})
    client.post(
        "/sessions",
        json={
            "campaign_id": campaign["id"],
            "session_date": "2026-06-08",
            "label": "Chapel",
            "raw_content": "The party found a silver key in the ruined chapel.",
            "author_display_name": "Player One",
        },
    )
    mock_client = MockOllamaClient("The silver key was in the chapel.")
    with patch("lore_goblin.answering.OllamaClient", return_value=mock_client):
        response = client.post(
            "/ask",
            json={
                "guild_id": "guild_test",
                "question": "Where is the silver key?",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert "silver key" in body["answer"].lower() or body["answer"]
    assert "PC roster" not in {citation.get("label") for citation in body.get("citations", [])}

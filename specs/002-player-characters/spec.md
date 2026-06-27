# Feature Specification: Player Characters

## User Story

Campaign owners and players can record the player character roster for a campaign so Lore Goblin has explicit, campaign-scoped knowledge of the main characters who appear throughout session notes.

## Scope

This feature includes:

- API support for creating and listing player characters.
- Campaign-scoped player character storage.
- Required player character name and notes.
- Discord `/lore pc` slash command for adding a player character to the linked campaign.
- Web UI support for adding and viewing player characters.
- Player character roster context during answer generation.

This feature excludes:

- Player character editing and deletion.
- Linking a player character to a Discord user.
- Permission enforcement for who may add player characters.
- Automatic extraction of player characters from session notes.
- Advanced player character-aware retrieval or relationship modeling.

## Functional Requirements

1. A user can add a player character to a campaign with a name and notes.
2. A player character is scoped to exactly one campaign.
3. Player character names cannot be blank.
4. Player character notes cannot be blank.
5. The API rejects attempts to add a player character to a missing campaign.
6. The API can list all player characters for a campaign.
7. The web UI can add a player character to the selected campaign.
8. The web UI shows the selected campaign's current player character roster.
9. A Discord user can add a player character to the linked campaign with `/lore pc`.
10. The Discord command reports a clear error when used outside a linked guild.
11. Lore Goblin includes the player character roster as structured context when answering campaign questions.

## Acceptance Criteria

- Given a campaign exists, when a web user submits a player character name and notes, then the character is stored and appears in the campaign roster.
- Given a Discord guild is linked to a campaign, when a user runs `/lore pc` with a name and notes, then the player character is stored in the linked campaign.
- Given a Discord guild is not linked, when a user runs `/lore pc`, then Lore Goblin explains that the server needs a linked campaign.
- Given the API receives a blank name or blank notes, when creating a player character, then it rejects the request.
- Given a campaign has multiple player characters, when the web UI loads the campaign, then it displays all of them.
- Given a campaign has player characters, when Lore Goblin answers a question, then roster details are available to the model as campaign context.

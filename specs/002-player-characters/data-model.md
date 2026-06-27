# Data Model: Player Characters

## Player Character

- `id`
- `campaign_id`
- `name`
- `notes`
- `created_at`
- `updated_at`

## Relationships

- A player character belongs to one campaign.
- A campaign can have many player characters.
- Deleting a campaign deletes its player characters.

# Data Model: MVP1

## Campaign

- `id`
- `name`
- `tone`
- `created_at`
- `updated_at`

## User

- `id`
- `display_name`
- `discord_user_id`
- `created_at`

## Campaign Member

- `id`
- `campaign_id`
- `user_id`
- `role`: `owner`, `admin`, or `player`

## Session

- `id`
- `campaign_id`
- `session_date`
- `label`
- `created_at`
- `updated_at`

## Session Note

- `id`
- `session_id`
- `campaign_id`
- `author_user_id`
- `raw_content`
- `created_at`
- `updated_at`

## Content Chunk

- `id`
- `campaign_id`
- `session_id`
- `source_type`
- `source_id`
- `chunk_index`
- `chunk_text`
- `created_at`

## Wiki Page

Wiki tables exist in MVP1 as scaffolding for generated drafts, but the approval workflow is outside MVP1.

## Discord Guild Link

- `id`
- `campaign_id`
- `guild_id`
- `created_at`

## Model Settings

- `id`
- `campaign_id`
- `provider`
- `chat_model`
- `base_url`


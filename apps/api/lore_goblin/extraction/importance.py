from __future__ import annotations

import sqlite3

RECENT_SESSION_BONUS = 5
MANUAL_PIN_BONUS = 10


def compute_importance_score(
    *,
    mention_count: int,
    session_count: int,
    relationship_count: int,
    unresolved_claim_count: int,
    manually_pinned: bool,
    recent_session_bonus: bool,
) -> float:
    score = (
        mention_count
        + session_count
        + relationship_count
        + unresolved_claim_count
        + (MANUAL_PIN_BONUS if manually_pinned else 0)
        + (RECENT_SESSION_BONUS if recent_session_bonus else 0)
    )
    return float(score)


def recompute_entity_importance(connection: sqlite3.Connection, campaign_id: str) -> None:
    entities = connection.execute(
        "SELECT id FROM entity WHERE campaign_id = ?",
        (campaign_id,),
    ).fetchall()
    recent_sessions = [
        row["id"]
        for row in connection.execute(
            """
            SELECT id
            FROM sessions
            WHERE campaign_id = ?
            ORDER BY session_date DESC, created_at DESC
            LIMIT 2
            """,
            (campaign_id,),
        ).fetchall()
    ]
    recent_session_ids = set(recent_sessions)

    for entity_row in entities:
        entity_id = entity_row["id"]
        mention_count = connection.execute(
            "SELECT COUNT(*) FROM entity_mention WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()[0]
        session_count = connection.execute(
            """
            SELECT COUNT(DISTINCT s.session_id)
            FROM entity_mention em
            JOIN source s ON s.id = em.source_id
            WHERE em.entity_id = ? AND s.session_id IS NOT NULL
            """,
            (entity_id,),
        ).fetchone()[0]
        relationship_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM relationship
            WHERE source_entity_id = ? OR target_entity_id = ?
            """,
            (entity_id, entity_id),
        ).fetchone()[0]
        unresolved_claim_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM claim
            WHERE (subject_entity_id = ? OR object_entity_id = ?)
              AND canon_status IN ('THEORY', 'DISPUTED', 'RUMOR')
            """,
            (entity_id, entity_id),
        ).fetchone()[0]
        existing = connection.execute(
            "SELECT manually_pinned, last_seen_session_id FROM entity_importance WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()
        manually_pinned = bool(existing["manually_pinned"]) if existing else False
        last_seen_session_id = existing["last_seen_session_id"] if existing else None

        latest_session = connection.execute(
            """
            SELECT s.session_id
            FROM entity_mention em
            JOIN source s ON s.id = em.source_id
            WHERE em.entity_id = ? AND s.session_id IS NOT NULL
            ORDER BY s.created_at DESC
            LIMIT 1
            """,
            (entity_id,),
        ).fetchone()
        if latest_session and latest_session["session_id"]:
            last_seen_session_id = latest_session["session_id"]

        recent_bonus = bool(last_seen_session_id and last_seen_session_id in recent_session_ids)
        score = compute_importance_score(
            mention_count=mention_count,
            session_count=session_count,
            relationship_count=relationship_count,
            unresolved_claim_count=unresolved_claim_count,
            manually_pinned=manually_pinned,
            recent_session_bonus=recent_bonus,
        )
        connection.execute(
            """
            INSERT INTO entity_importance (
                entity_id, mention_count, session_count, relationship_count,
                unresolved_claim_count, last_seen_session_id, importance_score,
                manually_pinned, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(entity_id) DO UPDATE SET
                mention_count = excluded.mention_count,
                session_count = excluded.session_count,
                relationship_count = excluded.relationship_count,
                unresolved_claim_count = excluded.unresolved_claim_count,
                last_seen_session_id = excluded.last_seen_session_id,
                importance_score = excluded.importance_score,
                manually_pinned = excluded.manually_pinned,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                entity_id,
                mention_count,
                session_count,
                relationship_count,
                unresolved_claim_count,
                last_seen_session_id,
                score,
                int(manually_pinned),
            ),
        )

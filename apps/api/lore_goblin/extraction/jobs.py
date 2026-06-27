from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from ..config import get_settings
from ..db import get_connection, new_id, row_to_dict
from .pipeline import run_extraction_pipeline, run_extraction_pipeline_with_clients

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

_executor: ThreadPoolExecutor | None = None
_executor_lock = Lock()


def get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="extraction")
        return _executor


def shutdown_executor() -> None:
    global _executor
    with _executor_lock:
        if _executor is not None:
            _executor.shutdown(wait=False, cancel_futures=False)
            _executor = None


def enqueue_extraction_job(source_id: str, campaign_id: str) -> dict:
    job_id = new_id("job")
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id, status
            FROM extraction_job
            WHERE source_id = ? AND status IN ('pending', 'running')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (source_id,),
        ).fetchone()
        if existing:
            return row_to_dict(existing)

        connection.execute(
            """
            INSERT INTO extraction_job (
                id, source_id, campaign_id, status, attempt_count
            )
            VALUES (?, ?, ?, 'pending', 0)
            """,
            (job_id, source_id, campaign_id),
        )
        row = connection.execute(
            "SELECT * FROM extraction_job WHERE id = ?",
            (job_id,),
        ).fetchone()
    job = row_to_dict(row)
    if get_settings().extraction_auto_run:
        get_executor().submit(_process_job, job["id"])
    return job


def get_extraction_status(source_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM extraction_job
            WHERE source_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (source_id,),
        ).fetchone()
    return row_to_dict(row) if row else None


def _process_job(job_id: str) -> None:
    settings = get_settings()
    max_retries = settings.max_extraction_retries
    with get_connection() as connection:
        job = connection.execute(
            "SELECT * FROM extraction_job WHERE id = ?",
            (job_id,),
        ).fetchone()
        if not job:
            return
        if job["status"] not in {"pending", "failed"}:
            return
        connection.execute(
            """
            UPDATE extraction_job
            SET status = 'running',
                attempt_count = attempt_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        source_id = job["source_id"]
        attempt_count = int(job["attempt_count"]) + 1

    try:
        run_extraction_pipeline(source_id)
    except Exception as exc:
        logger.exception("Extraction failed for source %s", source_id)
        with get_connection() as connection:
            if attempt_count >= max_retries:
                connection.execute(
                    """
                    UPDATE extraction_job
                    SET status = 'failed',
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (str(exc), job_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE extraction_job
                    SET status = 'pending',
                        error_message = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (str(exc), job_id),
                )
                get_executor().submit(_process_job, job_id)
        return

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE extraction_job
            SET status = 'complete',
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )


def run_job_sync_for_tests(
    job_id: str,
    *,
    chat_client,
    embed_client=None,
    extract_entities_fn=None,
    resolve_entities_fn=None,
    extract_claims_fn=None,
) -> None:
    with get_connection() as connection:
        job = connection.execute(
            "SELECT * FROM extraction_job WHERE id = ?",
            (job_id,),
        ).fetchone()
        if not job:
            return
        connection.execute(
            """
            UPDATE extraction_job
            SET status = 'running',
                attempt_count = attempt_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        source_id = job["source_id"]

    try:
        run_extraction_pipeline_with_clients(
            source_id,
            chat_client=chat_client,
            embed_client=embed_client,
            extract_entities_fn=extract_entities_fn,
            resolve_entities_fn=resolve_entities_fn,
            extract_claims_fn=extract_claims_fn,
        )
    except Exception as exc:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE extraction_job
                SET status = 'failed',
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(exc), job_id),
            )
        raise

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE extraction_job
            SET status = 'complete',
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )

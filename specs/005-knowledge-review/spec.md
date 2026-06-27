# Feature Specification: Knowledge Review

> Feature specs MUST follow the Development Workflow in `.specify/memory/constitution.md`.

**Feature Branch**: `005-knowledge-review`

**Created**: 2026-06-27

**Status**: Deferred (stub)

**Depends on**: `003-knowledge-extraction-pipeline`

**Input**: User description: "Web UI review queue for extracted entities, claims, and relationships. Approve, reject, edit, and promote canon status. Re-index on approval changes."

## Status

This feature is **deferred**. Specs 002–004 use **auto-index** for extracted knowledge. This stub captures future scope for human-in-the-loop review per Constitution Principle IV (web UI for review workflows).

## Planned User Scenarios (not yet prioritized)

### User Story 1 - Review Queue (Priority: TBD)

Campaign owner views a queue of flagged extractions: new major entities, conflicting claims, low-confidence resolutions.

### User Story 2 - Approve and Reject (Priority: TBD)

Owner approves, rejects, or edits extracted entities and claims before they affect canon.

### User Story 3 - Canon Promotion (Priority: TBD)

Owner promotes claim `canon_status` from `THEORY` to `CONFIRMED` or marks claims `DISPUTED`.

### User Story 4 - Re-index on Change (Priority: TBD)

Approved or edited knowledge triggers search index update.

## Out of Scope Until Activated

- Implementation tasks
- API endpoints
- Web UI components

## Activation Criteria

- Spec 003 extraction pipeline stable in production use
- Auto-index quality issues identified requiring human gate
- Maintainer runs `/speckit-specify` to expand this stub into full spec

## Assumptions

- Review is optional enhancement; not required for campaign-aware MVP (002–004).
- Web UI is the sole review surface (Discord remains ask/submit only).

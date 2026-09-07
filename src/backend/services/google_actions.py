from . import sync_store
from .google_calendar_client import create_event
from .google_tasks_client import create_task
from .notes import build_notes


def _destination(record: dict) -> str:
    if record.get("type") == "course" and record.get("due_date"):
        return "event"
    return "task"


def _push_one(record: dict) -> dict:
    notes = build_notes(record.get("overview"), record.get("steps") or [])
    destination = _destination(record)
    if destination == "event":
        result = create_event(
            title=record.get("title") or "(untitled)",
            description=notes,
            event_date=record["due_date"],
        )
    else:
        result = create_task(
            title=record.get("title") or "(untitled)",
            notes=notes,
            due_date=record.get("due_date"),
        )
    sync_store.mark_synced(record["source_id"], destination, result["id"])
    return {"kind": destination, "id": result["id"]}


def push_records(records: list[dict]) -> dict:
    synced = sync_store.load_sync_map()
    created = []
    skipped = []
    errors = []
    for record in records:
        source_id = record.get("source_id")
        if not source_id:
            continue
        if source_id in synced:
            skipped.append(source_id)
            continue
        try:
            result = _push_one(record)
            created.append({"source_id": source_id, **result})
        except Exception as err:
            errors.append({"source_id": source_id, "error": str(err)})
    return {"created": created, "skipped": skipped, "errors": errors}

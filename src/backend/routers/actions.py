from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import sync_store
from ..services.google_calendar_client import create_event
from ..services.google_tasks_client import create_task
from ..services.notes import build_notes
from ..services.pipeline import TASKS_PATH
from ..utils import read_json

router = APIRouter(prefix="/api/actions", tags=["actions"])


class PushRequest(BaseModel):
    source_id: str


def _find_record(source_id: str):
    records, _, _ = read_json(TASKS_PATH)
    for r in records:
        if r.get("source_id") == source_id:
            return r
    return None


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


@router.get("/status")
def status():
    return {"synced": sync_store.load_sync_map()}


@router.post("/push")
def push(body: PushRequest):
    synced = sync_store.load_sync_map()
    if body.source_id in synced:
        return {"status": "already_synced", **synced[body.source_id]}

    record = _find_record(body.source_id)
    if not record:
        raise HTTPException(404, "Record not found in the last run's output.")

    try:
        result = _push_one(record)
    except Exception as err:  
        raise HTTPException(502, f"Google API error: {err}") from err
    return {"status": "created", **result}


@router.post("/push-all")
def push_all():
    records, _, _ = read_json(TASKS_PATH)
    synced = sync_store.load_sync_map()
    created = []
    skipped = []
    errors = []
    for r in records:
        sid = r.get("source_id")
        if not sid:
            continue
        if sid in synced:
            skipped.append(sid)
            continue
        try:
            result = _push_one(r)
            created.append({"source_id": sid, **result})
        except Exception as err: 
            errors.append({"source_id": sid, "error": str(err)})
    return {"created": created, "skipped": skipped, "errors": errors}

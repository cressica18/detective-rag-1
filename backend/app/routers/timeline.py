"""Timeline router."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import TimelineEvent
from app.repositories import sqlite_repo

router = APIRouter()


@router.get("/timeline/{case_id}", response_model=list[TimelineEvent])
async def get_timeline(case_id: str):
    events = sqlite_repo.get_timeline_events(case_id)
    if events is None:
        raise HTTPException(404, f"Case {case_id} not found")
    return [
        TimelineEvent(
            event_id=e["event_id"],
            timestamp=e["timestamp"],
            description=e["description"],
            source_doc_ids=e["source_doc_ids"],
            is_contradicted=e["is_contradicted"]
        )
        for e in events
    ]

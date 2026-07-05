"""Suspects router — returns suspect scores and relationship graph."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import SuspectsResponse, Suspect, RelationshipEdge
from app.repositories import sqlite_repo
from app.services.graph_builder import build_relationship_graph

router = APIRouter()


@router.get("/suspects/{case_id}", response_model=SuspectsResponse)
async def get_suspects(case_id: str):
    suspects_data = sqlite_repo.get_suspects(case_id)
    suspects = [
        Suspect(
            name=s["name"],
            role=s.get("role", "unknown"),
            opportunity_score=s["opportunity_score"],
            motive_score=s["motive_score"],
            contradiction_count=s["contradiction_count"],
            evidence_strength=s["evidence_strength"],
            total_score=s["total_score"],
            motive_summary=s.get("motive_summary", "")
        )
        for s in suspects_data
    ]

    # Build graph
    try:
        graph = build_relationship_graph(case_id)
        edges = [
            RelationshipEdge(
                source=e["source"],
                target=e["target"],
                relation_type=e["label"],
                evidence_doc_ids=e["data"].get("evidence_doc_ids", []),
                weight=float(e["data"].get("weight", 1))
            )
            for e in graph.get("edges", [])
        ]
    except Exception:
        edges = []

    return SuspectsResponse(suspects=suspects, edges=edges)


@router.get("/suspects/{case_id}/graph")
async def get_graph(case_id: str):
    """Returns raw react-flow graph data."""
    try:
        graph = build_relationship_graph(case_id)
        return graph
    except Exception as e:
        raise HTTPException(500, str(e))

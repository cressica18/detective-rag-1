"""Graph builder — builds relationship graph using networkx, exports for react-flow."""
import networkx as nx
from collections import defaultdict
from app.repositories import sqlite_repo
from app.utils.logging import get_logger

logger = get_logger(__name__)

DOC_TYPE_RELATION = {
    "witness_statement": "witnessed together",
    "interview": "interviewed regarding",
    "phone_record": "communicated with",
    "cctv_transcript": "observed with",
    "security_log": "co-located",
    "police_report": "mentioned in report",
    "forensic_report": "connected by evidence",
    "evidence_inventory": "linked by evidence",
    "autopsy_report": "linked by evidence",
    "unknown": "associated with",
}


def build_relationship_graph(case_id: str) -> dict:
    """
    Build a relationship graph from entity co-mentions.
    Returns: {"nodes": [...], "edges": [...]} for react-flow.
    """
    # Get all people per document
    entities = sqlite_repo.get_entities(case_id, entity_type="person")
    documents = {d["doc_id"]: d for d in sqlite_repo.get_documents(case_id)}
    suspects = {s["name"].lower(): s for s in sqlite_repo.get_suspects(case_id)}
    contradictions = sqlite_repo.get_contradictions(case_id)

    # Group people by document
    doc_people: dict[str, list[str]] = defaultdict(list)
    all_people: set[str] = set()
    for entity in entities:
        name = entity["value"].strip()
        if name and len(name) >= 3:
            doc_people[entity["doc_id"]].append(name)
            all_people.add(name)

    G = nx.Graph()

    # Add all nodes
    for person in all_people:
        key = person.lower()
        suspect_data = suspects.get(key, {})
        G.add_node(person, **{
            "total_score": suspect_data.get("total_score", 0),
            "role": suspect_data.get("role", "unknown"),
        })

    # Add edges from document co-mentions
    for doc_id, people_in_doc in doc_people.items():
        doc = documents.get(doc_id, {})
        doc_type = doc.get("doc_type", "unknown")
        relation = DOC_TYPE_RELATION.get(doc_type, "associated with")

        unique_people = list(set(people_in_doc))
        for i in range(len(unique_people)):
            for j in range(i + 1, len(unique_people)):
                p1, p2 = unique_people[i], unique_people[j]
                if G.has_edge(p1, p2):
                    G[p1][p2]["weight"] = G[p1][p2].get("weight", 1) + 1
                    if relation not in G[p1][p2]["relations"]:
                        G[p1][p2]["relations"].append(relation)
                else:
                    G.add_edge(p1, p2, weight=1, relations=[relation],
                               doc_ids=[doc_id], relation_type=relation)

    # Add contradiction edges
    for c in contradictions:
        # Find people involved
        claim_a_text = c["claim_a"].lower()
        claim_b_text = c["claim_b"].lower()
        for person in all_people:
            if person.lower() in claim_a_text:
                for other in all_people:
                    if other != person and other.lower() in claim_b_text:
                        if G.has_edge(person, other):
                            G[person][other]["relations"].append("conflicting statement with")
                        else:
                            G.add_edge(person, other, weight=2, relations=["conflicting statement with"],
                                       doc_ids=[], relation_type="conflicting statement with")

    # Export to react-flow format
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": node_id,
            "data": {
                "label": node_id,
                "role": data.get("role", "unknown"),
                "total_score": data.get("total_score", 0),
            },
            "position": {"x": 0, "y": 0},  # react-flow will layout
            "type": "suspectNode",
        })

    edges = []
    edge_id = 0
    for u, v, data in G.edges(data=True):
        relation = data.get("relation_type", "associated with")
        relations = data.get("relations", [relation])
        # Use the most "interesting" relation
        if "conflicting statement with" in relations:
            relation = "conflicting statement with"
        elif "communicated with" in relations:
            relation = "communicated with"

        edges.append({
            "id": f"e{edge_id}",
            "source": u,
            "target": v,
            "label": relation,
            "data": {
                "relation_type": relation,
                "weight": data.get("weight", 1),
                "evidence_doc_ids": data.get("doc_ids", []),
            },
            "type": "suspectEdge",
        })
        edge_id += 1

    logger.info(f"Graph built: {len(nodes)} nodes, {len(edges)} edges for case {case_id}")
    return {"nodes": nodes, "edges": edges}

"""Prompt builder — constructs system + user prompt with [S#] citation tags."""

SYSTEM_PROMPT = """You are a meticulous case analyst working on a criminal investigation. 
Your role is to answer questions based ONLY on the provided case file excerpts.

RULES:
1. Only use information from the numbered source excerpts provided. Do not invent facts.
2. If the answer cannot be found in the sources, say: "This information is not available in the case file."
3. Cite your sources using [S1], [S2], etc. tags immediately after the relevant claim.
4. Be precise about times, names, and locations.
5. Maintain a professional, analytical tone — as if writing a case analysis memo.
6. If sources conflict on a point, note the conflict explicitly and cite both sources.
"""


def build_chat_prompt(chunks: list[dict], question: str, history: list[dict]) -> str:
    """Build the full prompt for a chat query."""
    # Build source blocks
    source_blocks = []
    for i, chunk in enumerate(chunks, 1):
        doc_type = chunk.get("doc_type", "unknown").replace("_", " ").upper()
        filename = chunk.get("filename", "unknown")
        page = chunk.get("page", 1)
        source_blocks.append(
            f"[S{i}] SOURCE: {doc_type} | File: {filename} | Page: {page}\n{chunk['text']}"
        )

    sources_text = "\n\n---\n\n".join(source_blocks)

    # Build conversation history
    history_text = ""
    if history:
        recent = history[-6:]  # last 3 turns
        history_lines = []
        for turn in recent:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            history_lines.append(f"[{role.upper()}]: {content}")
        history_text = "\n".join(history_lines) + "\n\n"

    prompt = f"""CASE FILE EXCERPTS:

{sources_text}

---

{history_text}INVESTIGATOR QUERY: {question}

Please provide a thorough answer based on the case file excerpts above. 
Use [S1], [S2], etc. to cite specific sources. Be precise."""

    return prompt


def build_entity_extraction_prompt(text: str, filename: str) -> str:
    """Prompt for structured entity extraction from a document."""
    return f"""Extract all entities from this case document excerpt.

Document: {filename}

TEXT:
{text[:3000]}

Return ONLY a valid JSON object with these exact keys:
{{
  "people": [
    {{"name": "Full Name", "role": "their role/description"}}
  ],
  "times": [
    {{"raw": "original time string", "normalized": "HH:MM if parseable or null", "context": "what happened at this time"}}
  ],
  "locations": ["location name"],
  "objects": ["relevant physical object or evidence item"],
  "claims": [
    {{"person": "name", "time": "time if mentioned", "location": "location if mentioned", "action": "what they did or claimed"}}
  ]
}}"""


def build_contradiction_check_prompt(claim_a: str, source_a: str, claim_b: str, source_b: str) -> str:
    """Prompt to check if two claims genuinely conflict."""
    return f"""Two statements from a criminal investigation:

STATEMENT A (from {source_a}):
{claim_a}

STATEMENT B (from {source_b}):
{claim_b}

Do these statements genuinely conflict with each other, or are they compatible?
Return ONLY valid JSON:
{{"conflict": true/false, "explanation": "brief explanation of why they conflict or are compatible"}}"""


def build_motive_score_prompt(suspect_name: str, relevant_text: str) -> str:
    """Prompt to score motive strength for a suspect."""
    return f"""Analyze the following case file excerpts regarding {suspect_name} for evidence of motive.

EXCERPTS:
{relevant_text[:2500]}

Score the strength of {suspect_name}'s motive on a scale of 0-100:
- 0: No motive evidence found
- 25: Weak motive (minor dispute, distant connection)  
- 50: Moderate motive (financial interest, personal conflict)
- 75: Strong motive (direct financial gain, serious grievance)
- 100: Very strong motive (imminent threat, major financial crime, serious personal vendetta)

Return ONLY valid JSON:
{{"score": <0-100 integer>, "summary": "one sentence summarizing the motive"}}"""


def build_summary_prompt(case_id: str, suspects: list[dict], contradictions: list[dict],
                          timeline: list[dict], chunks: list[dict]) -> str:
    """Prompt to generate the final case summary."""
    suspect_text = "\n".join([
        f"- {s['name']} (role: {s.get('role','unknown')}): total score {s['total_score']:.0f}/100 "
        f"(opportunity={s['opportunity_score']:.0f}, motive={s['motive_score']:.0f}, "
        f"contradictions={s['contradiction_count']}, evidence={s['evidence_strength']:.0f})"
        for s in suspects
    ])

    contradiction_text = "\n".join([
        f"- CONFLICT #{i+1}: \"{c['claim_a']}\" vs \"{c['claim_b']}\" — {c['explanation']}"
        for i, c in enumerate(contradictions[:5])
    ])

    timeline_text = "\n".join([
        f"- {e['timestamp']}: {e['description']}" + (" [CONTRADICTED]" if e.get('is_contradicted') else "")
        for e in timeline[:15]
    ])

    source_blocks = []
    for i, chunk in enumerate(chunks[:5], 1):
        source_blocks.append(f"[S{i}] {chunk.get('filename','')}: {chunk['text'][:300]}")
    sources_text = "\n\n".join(source_blocks)

    return f"""Generate a detective-style Case Closure Report for this investigation.

SUSPECTS AND SCORES:
{suspect_text}

DETECTED CONTRADICTIONS:
{contradiction_text}

RECONSTRUCTED TIMELINE:
{timeline_text}

KEY EVIDENCE EXCERPTS:
{sources_text}

Write a formal detective case closure report that:
1. Identifies the prime suspect and explains why, citing evidence
2. Explains the key contradiction(s) that break their alibi
3. Summarizes the motive
4. States your confidence level (as a percentage)
5. Notes which other suspects were investigated and cleared

Use [S1], [S2], etc. to cite the evidence excerpts where relevant.
Write in a professional, procedural detective tone — terse, factual, citing evidence.
End with a verdict line: "VERDICT: [Name] is the prime suspect. Confidence: [X]%"
"""


def build_batch_contradiction_prompt(pairs: list[dict]) -> str:
    """Batch multiple candidate contradiction pairs into a single prompt."""
    blocks = []
    for p in pairs:
        blocks.append(
            f"PAIR {p['index']} (person: {p['person']}):\n"
            f"  Statement A (source: {p['source_a']}): \"{p['claim_a']}\"\n"
            f"  Statement B (source: {p['source_b']}): \"{p['claim_b']}\""
        )
    pairs_text = "\n\n".join(blocks)
    return f"""You will be shown several pairs of statements extracted from a criminal investigation's
case documents. Each pair references the same person and an approximate time or location.
For EACH pair, decide whether the two statements genuinely conflict (cannot both be true) or are compatible.

{pairs_text}

Respond ONLY with a valid JSON array, one object per pair, in this exact form:
[{{"index": <pair number>, "conflict": true|false, "explanation": "<one sentence>"}}]"""


def build_batch_motive_prompt(suspects: list[dict]) -> str:
    """Batch motive scoring for multiple suspects into a single prompt."""
    blocks = []
    for s in suspects:
        blocks.append(f"SUSPECT: {s['name']}\nEXCERPTS:\n{s['text'][:1500]}")
    suspects_text = "\n\n---\n\n".join(blocks)
    return f"""Analyze the following case file excerpts for each suspect and score the strength
of their motive on a scale of 0-100:
- 0: No motive evidence found
- 25: Weak motive (minor dispute, distant connection)
- 50: Moderate motive (financial interest, personal conflict)
- 75: Strong motive (direct financial gain, serious grievance)
- 100: Very strong motive (imminent threat, major financial crime, serious personal vendetta)

{suspects_text}

Respond ONLY with a valid JSON array, one object per suspect, in this exact form:
[{{"name": "<suspect name>", "score": <0-100 integer>, "summary": "<one sentence>"}}]"""
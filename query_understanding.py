"""Groq-powered query understanding: pull professors/classes out of a query.

Given a user question, a Groq LLM extracts any course titles and professor
names mentioned. The result is returned as structured JSON and used by the
retrieval step (embed_store.retrieve) to add ChromaDB metadata filtering, so a
question about "CS 252" only matches CS 252 reviews.

Schema returned by extract_entities():
    {"classes": ["CS 252", ...], "professors": ["Rodriguez-Rivera", ...]}

Requires a real GROQ_API_KEY in .env (the template ships a placeholder).
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Groq-hosted model. llama-3.3-70b is strong at structured extraction and
# supports JSON-mode responses.
MODEL = "llama-3.3-70b-versatile"

# The extraction instruction. It pins down the JSON schema, normalization rules,
# and a "do not invent" guard so the model only reports entities actually in the
# query. The examples are the ones from planning.md, expanded to show the exact
# JSON shape and the empty-array / professor-only cases.
SYSTEM_PROMPT = """\
You are an entity extractor for a Purdue Computer Science course-review search \
system. From the user's query, identify any course titles and professor names \
that are explicitly mentioned.

Rules:
- A course title is a department prefix plus a 3-digit number (e.g. "CS 240", \
"MA 261"). If the query gives only a bare 3-digit number in a CS context, \
prefix it with "CS". Normalize every course to "<DEPT> <NUMBER>" with one space \
(e.g. "cs240" -> "CS 240").
- A professor is a person's name; a last name alone is fine. Return it as \
written in the query (do not add titles like "Professor" or "Dr.").
- Only extract entities that actually appear in the query. Do NOT guess or \
invent professors or classes that are not mentioned.
- If no classes are mentioned, use an empty list; likewise for professors.
- Respond with ONLY a single JSON object and nothing else (no prose, no \
markdown fences) using exactly this schema:
  {"classes": [<strings>], "professors": [<strings>]}

Examples:
Query: What are some downsides of CS 240
{"classes": ["CS 240"], "professors": []}

Query: Is Turkstra a good professor for CS 240
{"classes": ["CS 240"], "professors": ["Turkstra"]}

Query: Who teaches 182 and are they any good
{"classes": ["CS 182"], "professors": []}

Query: Who are the best-regarded CS professors
{"classes": [], "professors": []}\
"""

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key or key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add your real Groq key to .env "
                "(see .env.example)."
            )
        _client = Groq(api_key=key)
    return _client


def extract_entities(query: str) -> dict:
    """Extract {"classes": [...], "professors": [...]} from a query via Groq.

    Falls back to empty lists if the model returns anything unparseable, so a
    bad extraction degrades to an unfiltered (plain semantic) search rather than
    crashing the pipeline.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,  # deterministic extraction
        response_format={"type": "json_object"},  # enforce JSON output
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}"},
        ],
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"classes": [], "professors": []}

    classes = [str(c).strip() for c in data.get("classes", []) if str(c).strip()]
    professors = [str(p).strip() for p in data.get("professors", []) if str(p).strip()]
    return {"classes": classes, "professors": professors}


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Is Turkstra good for CS 240?"
    print(json.dumps(extract_entities(q), indent=2))

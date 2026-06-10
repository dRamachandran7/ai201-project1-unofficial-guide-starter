"""Grounded response generation — the final stage of the pipeline.

Ties the whole system together (Milestone 5):

    query
      -> embed_store.search()         # Groq entity extraction + metadata-filtered
                                      # ChromaDB retrieval (top-k = 5)
      -> format retrieved chunks as numbered sources
      -> Groq llama-3.3-70b-versatile # answer grounded ONLY in those sources

The system prompt forbids the model from using outside knowledge, so answers
stay attributable to the retrieved Rate My Professors reviews.

Run interactively:   python generate.py
One-shot question:    python generate.py "Who teaches CS 252?"
Requires a real GROQ_API_KEY in .env.
"""

from __future__ import annotations

import sys

from query_understanding import MODEL, _get_client
from embed_store import search

# Grounding instruction. The required line is included verbatim; the rest tells
# the model how to use the numbered sources and what to do when they fall short.
SYSTEM_PROMPT = """\
You are The Unofficial Guide, an assistant that answers questions about Purdue \
Computer Science professors and courses using student reviews from Rate My \
Professors.

Use only the information from the retrieved sources, do not use general \
information to respond to a user's prompt.

Guidelines:
- Base every claim on the numbered sources provided below. Cite the sources you \
rely on by their number, e.g. [1], [3].
- When sources name the professor or class, attribute opinions to them.
- Reviews can be subjective, satirical, or contradictory; reflect genuine \
disagreement rather than flattening it, and don't treat one review as fact.
- If the sources do not contain enough information to answer, say so plainly \
instead of guessing.\
"""


def format_context(hits: list[dict]) -> str:
    """Render retrieved chunks as numbered sources for the prompt."""
    if not hits:
        return "(no sources retrieved)"
    lines = []
    for i, h in enumerate(hits, start=1):
        m = h["metadata"]
        lines.append(
            f"[{i}] Professor {m['professor']} — {m['class']} "
            f"(source: {m.get('source_url', 'N/A')})\n"
            f"    \"{h['document'].strip()}\""
        )
    return "\n".join(lines)


def format_citations(hits: list[dict]) -> str:
    """Build a deduped, attributable source list (professor, class, RMP link).

    Source attribution for the final response: each distinct review page the
    answer drew from is listed once with its Rate My Professors URL.
    """
    seen: set[str] = set()
    lines: list[str] = []
    for h in hits:
        m = h["metadata"]
        url = m.get("source_url", "")
        if url in seen:
            continue
        seen.add(url)
        lines.append(f"- {m['professor']} ({m['class']}) — Rate My Professors: {url}")
    return "Sources:\n" + "\n".join(lines) if lines else "Sources: (none)"


def generate_answer(query: str) -> dict:
    """Retrieve grounding chunks and generate a grounded answer.

    Returns {"answer": str, "sources": list[hit]} so callers can show both the
    response and the chunks it was grounded in.
    """
    hits = search(query)
    context = format_context(hits)

    user_message = (
        f"Question: {query}\n\n"
        f"Retrieved sources:\n{context}\n\n"
        "Answer the question using only the sources above."
    )

    response = _get_client().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = response.choices[0].message.content.strip()
    return {
        "answer": answer,
        "sources": hits,
        "citations": format_citations(hits),
    }


def _print_result(query: str, result: dict) -> None:
    print(f"\nQ: {query}\n")
    print(result["answer"])
    print("\n" + result["citations"])


def main() -> None:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        _print_result(query, generate_answer(query))
        return

    print("The Unofficial Guide — ask about Purdue CS professors/courses.")
    print("(empty line or Ctrl-D to quit)")
    try:
        while True:
            query = input("\n> ").strip()
            if not query:
                break
            _print_result(query, generate_answer(query))
    except EOFError:
        pass


if __name__ == "__main__":
    main()

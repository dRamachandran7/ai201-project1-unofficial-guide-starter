"""Embed review chunks into ChromaDB and retrieve relevant chunks for a query.

This is the Milestone 4 (embedding + vector store + retrieval) stage of the
pipeline described in planning.md:

    Chunking (chunk_reviews.py -> chunks.json)
      -> Embedding:  sentence-transformers all-MiniLM-L6-v2
      -> Vector store: ChromaDB, collection.add(documents, embeddings, ids, metadatas)
      -> Retrieval:  top-k = 3 chunks per query

Two entry points:
  - build_index():  read chunks.json, embed every chunk, and add them to a
    persistent ChromaDB collection with their ids + metadata.
  - retrieve(query, top_k=3):  embed the prompt and return the most relevant
    chunks (with metadata + distance) for use as grounding context downstream.

Run `python embed_store.py` to (re)build the index, then drop into a small
interactive prompt to test retrieval. Pass a query as an argument to do a
one-shot retrieval, e.g.  python embed_store.py "Who teaches CS 252?"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path(__file__).parent / "chunks.json"
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "rmp_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3  # planning.md: top-k of 3
BATCH_SIZE = 256

# Cache the model and client so repeated retrieve() calls don't reload them.
_model: SentenceTransformer | None = None
_client: chromadb.ClientAPI | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection() -> chromadb.Collection:
    """Return the reviews collection, creating it if needed (cosine space)."""
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(reset: bool = True) -> chromadb.Collection:
    """Embed every chunk in chunks.json and add it to ChromaDB.

    With reset=True the collection is dropped first so rebuilds are clean and
    don't accumulate stale chunks from a previous chunk size.
    """
    if not CHUNKS_FILE.exists():
        raise SystemExit(f"{CHUNKS_FILE.name} not found. Run chunk_reviews.py first.")

    records = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    if not records:
        raise SystemExit("chunks.json is empty.")

    client = get_client()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet
    collection = get_collection()

    documents = [r["document"] for r in records]
    ids = [r["id"] for r in records]
    metadatas = [r["metadata"] for r in records]

    model = get_model()
    print(f"Embedding {len(documents)} chunks with {EMBED_MODEL} ...")
    embeddings = model.encode(
        documents,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).tolist()

    # Add in batches to stay well under ChromaDB's per-call limits.
    for start in range(0, len(documents), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.add(
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            ids=ids[start:end],
            metadatas=metadatas[start:end],
        )

    print(f"Indexed {collection.count()} chunks into '{COLLECTION_NAME}' at {CHROMA_DIR.name}/")
    return collection


def retrieve(query: str, top_k: int = TOP_K, where: dict | None = None) -> list[dict]:
    """Return the top_k most relevant chunks for a prompt.

    The query is embedded with the same model used for indexing, then matched
    against the collection by cosine distance. An optional `where` filter maps
    onto chunk metadata (e.g. {"class": "CS252"}) to scope retrieval.

    Each result is a dict: {document, metadata, distance}.
    """
    collection = get_collection()
    if collection.count() == 0:
        raise SystemExit("Collection is empty. Run build_index() first.")

    query_embedding = get_model().encode([query], convert_to_numpy=True).tolist()
    result = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where,
    )

    hits: list[dict] = []
    for doc, meta, dist in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        hits.append({"document": doc, "metadata": meta, "distance": dist})
    return hits


_known_professors: list[str] | None = None


def get_known_professors() -> list[str]:
    """Return the distinct professor names stored in the collection (cached)."""
    global _known_professors
    if _known_professors is None:
        metas = get_collection().get(include=["metadatas"])["metadatas"]
        _known_professors = sorted({m["professor"] for m in metas if m.get("professor")})
    return _known_professors


def build_where_filter(entities: dict) -> dict | None:
    """Turn extracted {classes, professors} into a ChromaDB `where` filter.

    - Classes are normalized to the metadata format ("CS 252" -> "CS252").
    - Professor names from the query (often just a last name) are matched against
      the full names stored in metadata, so "Turkstra" -> "Jeff Turkstra".
    Conditions are combined with $and; returns None when nothing matched (so the
    caller falls back to an unfiltered semantic search).
    """
    conditions: list[dict] = []

    classes = {c.replace(" ", "").upper() for c in entities.get("classes", [])}
    if classes:
        conditions.append({"class": {"$in": sorted(classes)}})

    wanted = [p.lower() for p in entities.get("professors", [])]
    if wanted:
        matches = sorted({
            full for full in get_known_professors()
            if any(w in full.lower() for w in wanted)
        })
        if matches:
            conditions.append({"professor": {"$in": matches}})

    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


def search(query: str, top_k: int = TOP_K) -> list[dict]:
    """Full retrieval: extract entities via Groq, filter on metadata, retrieve.

    If the metadata filter returns no hits (e.g. the reviewer-stated class never
    matched), it retries without the filter so the query still gets an answer.
    """
    from query_understanding import extract_entities

    entities = extract_entities(query)
    where = build_where_filter(entities)
    hits = retrieve(query, top_k=top_k, where=where)
    if not hits and where is not None:
        hits = retrieve(query, top_k=top_k)
    return hits


def _print_hits(query: str, hits: list[dict]) -> None:
    print(f"\nQuery: {query}")
    for i, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        print(f"\n  [{i}] {m['professor']} ({m['class']})  distance={hit['distance']:.3f}")
        print(f"      {hit['document']}")


def main() -> None:
    # One-shot retrieval if a query is passed on the command line.
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        _print_hits(query, retrieve(query))
        return

    build_index()
    print("\nIndex ready. Type a question to retrieve (empty line / Ctrl-D to quit).")
    try:
        while True:
            query = input("\n> ").strip()
            if not query:
                break
            _print_hits(query, retrieve(query))
    except EOFError:
        pass


if __name__ == "__main__":
    main()

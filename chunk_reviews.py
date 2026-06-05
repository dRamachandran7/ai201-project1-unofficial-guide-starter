"""Chunk scraped Rate My Professors reviews for embedding into ChromaDB.

Reads the plain-text files produced by scrape_reviews.py in documents/, and for
each review chunks ONLY the free-text comment (everything after the "Comment:"
flag), per the Chunking Strategy in planning.md:

  - Chunk size: 90 characters
  - Overlap:    20 characters

The header lines and the per-review metadata line (Class/Quality/etc.) are NOT
chunked as text. Instead the professor name and class are captured as structured
metadata and attached to every chunk, so ChromaDB can filter on them later
(e.g. "reviews where class == CS252").

Output: chunks.json in the project root, a list of records shaped for a
ChromaDB collection.add(...) call:
    {"id": ..., "document": <chunk text>, "metadata": {professor, class, ...}}

This is the Milestone 3 (chunking) stage; Milestone 4 reads chunks.json, embeds
each document, and adds it to ChromaDB with the same ids/metadatas.
"""

from __future__ import annotations

import json
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"
OUTPUT_FILE = Path(__file__).parent / "chunks.json"

CHUNK_SIZE = 165  # characters per chunk (planning.md)
OVERLAP = 20  # characters of overlap between consecutive chunks (planning.md)
COMMENT_FLAG = "Comment: "
REVIEW_DELIM = "--- Review "


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split text into fixed-size character chunks with overlap.

    The window advances by (size - overlap) each step so consecutive chunks
    share `overlap` characters, preserving context across boundaries. Comments
    shorter than `size` yield a single chunk.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    step = size - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than chunk size")

    chunks = []
    for start in range(0, len(text), step):
        chunk = text[start : start + size]
        chunks.append(chunk)
        if start + size >= len(text):
            break  # last window already reached the end
    return chunks


def parse_header(lines: list[str]) -> dict:
    """Extract professor-level metadata from the header block."""
    header: dict[str, str] = {}
    for line in lines:
        if line.startswith("Professor: "):
            header["professor"] = line[len("Professor: "):].strip()
        elif line.startswith("Department: "):
            header["department"] = line[len("Department: "):].strip()
        elif line.startswith("Course (from planning.md): "):
            header["course"] = line[len("Course (from planning.md): "):].strip()
        elif line.startswith("Source: "):
            header["source_url"] = line[len("Source: "):].strip()
    return header


def parse_class(meta_line: str) -> str:
    """Pull the class code out of a review's metadata line.

    Example line: "Class: CS240 | Date: 2026-05-07 | Quality: 3/5 | ..."
    """
    for field in meta_line.split(" | "):
        if field.startswith("Class: "):
            return field[len("Class: "):].strip()
    return "Unknown"


def parse_reviews(file_text: str) -> tuple[dict, list[dict]]:
    """Split a professor file into (header metadata, list of reviews).

    Each review is {"class": ..., "comment": ...}; comments marked
    "(no comment)" or empty are dropped since there is nothing to embed.
    """
    # Header is everything before the first review delimiter.
    head, _, body = file_text.partition("\n" + REVIEW_DELIM)
    header = parse_header(head.splitlines())

    reviews: list[dict] = []
    # Re-prepend the delimiter we split on, then split into review blocks.
    body = REVIEW_DELIM + body if body else ""
    blocks = body.split(REVIEW_DELIM)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        cls = "Unknown"
        comment = ""
        for line in block.splitlines():
            if line.startswith("Class: "):
                cls = parse_class(line)
            elif line.startswith(COMMENT_FLAG):
                comment = line[len(COMMENT_FLAG):].strip()
        if not comment or comment == "(no comment)":
            continue
        reviews.append({"class": cls, "comment": comment})
    return header, reviews


def build_chunks() -> list[dict]:
    """Parse every document file and produce ChromaDB-ready chunk records."""
    records: list[dict] = []
    files = sorted(DOCUMENTS_DIR.glob("*.txt"))
    if not files:
        raise SystemExit(f"No .txt files in {DOCUMENTS_DIR}. Run scrape_reviews.py first.")

    for path in files:
        header, reviews = parse_reviews(path.read_text(encoding="utf-8"))
        stem = path.stem  # e.g. "Turkstra_2231495" -> stable id prefix
        for r_idx, review in enumerate(reviews, start=1):
            chunks = chunk_text(review["comment"])
            for c_idx, chunk in enumerate(chunks):
                records.append({
                    "id": f"{stem}_r{r_idx}_c{c_idx}",
                    "document": chunk,
                    "metadata": {
                        "professor": header.get("professor", "Unknown"),
                        "class": review["class"],
                        "course": header.get("course", ""),
                        "department": header.get("department", ""),
                        "source_url": header.get("source_url", ""),
                        "review_index": r_idx,
                        "chunk_index": c_idx,
                    },
                })
        print(f"{path.name:<32} {len(reviews):>4} reviews")
    return records


def main() -> None:
    records = build_chunks()
    OUTPUT_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    n_reviews = len({(r["metadata"]["professor"], r["metadata"]["review_index"]) for r in records})
    print(f"\nWrote {len(records)} chunks from {n_reviews} reviews -> {OUTPUT_FILE.name}")
    print("Each record has document + metadata (professor, class, ...) ready for ChromaDB.")


if __name__ == "__main__":
    main()

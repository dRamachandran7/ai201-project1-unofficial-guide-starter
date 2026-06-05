"""Scrape Rate My Professors reviews into plain-text files for later chunking.

RateMyProfessors is a JavaScript-rendered React app, so the review text is not
present in the raw HTML. Instead, the site exposes a GraphQL API that the front
end calls. This script queries that API directly:

  - Each professor's page URL ends in a numeric legacy id, e.g.
    https://www.ratemyprofessors.com/professor/2231495  ->  2231495
  - The GraphQL "node" id is base64("Teacher-<legacy_id>").
  - The public API accepts the well-known anonymous "Basic dGVzdDp0ZXN0"
    (test:test) authorization header that the site itself ships.

For every professor listed below we page through all of their ratings and write
one UTF-8 text file per professor into documents/. Each file starts with a short
header (name, department, course label from planning.md, overall stats) followed
by one block per review. The plain-text layout is intentionally simple so the
Milestone 3 chunker can split it without parsing HTML or JSON.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path

import requests

GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
# Public anonymous credential shipped by the RMP front end (test:test).
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; unofficial-guide-scraper/1.0)",
}
OUTPUT_DIR = Path(__file__).parent / "documents"
PAGE_SIZE = 100  # ratings fetched per GraphQL request
REQUEST_PAUSE = 0.5  # seconds between requests, to be polite to the API


# Professors from planning.md. The first source (school id 783) is a search
# listing, not a professor page, so it is not scraped here. The "course" label
# is the class noted in planning.md and is recorded as context in the output.
@dataclass(frozen=True)
class Professor:
    legacy_id: str
    course: str  # course label from planning.md (context only)


PROFESSORS = [
    Professor("2231495", "CS 240"),
    Professor("2120117", "MGMT / CS 177"),
    Professor("2656983", "CS 251"),
    Professor("1931762", "CS 250"),
    Professor("132641", "CS 252"),
    Professor("2931186", "CS 182"),
    Professor("2523519", "CS 180"),
    Professor("2507062", "CS 180 (dept. head)"),
    Professor("132647", "CS 182"),
]

TEACHER_QUERY = """
query Teacher($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      department
      school { name }
      avgRating
      avgDifficulty
      numRatings
      wouldTakeAgainPercent
      ratings(first: %d, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            class
            comment
            date
            qualityRating
            difficultyRatingRounded
            wouldTakeAgain
            grade
            attendanceMandatory
            ratingTags
            thumbsUpTotal
            thumbsDownTotal
            isForOnlineClass
          }
        }
      }
    }
  }
}
""" % PAGE_SIZE


def node_id_for(legacy_id: str) -> str:
    """Return the base64 GraphQL node id for a professor's legacy id."""
    return base64.b64encode(f"Teacher-{legacy_id}".encode()).decode()


def fetch_professor(legacy_id: str) -> dict:
    """Fetch a professor's profile plus every rating, paging through the API."""
    node_id = node_id_for(legacy_id)
    cursor = None
    teacher: dict | None = None
    ratings: list[dict] = []

    while True:
        resp = requests.post(
            GRAPHQL_URL,
            json={"query": TEACHER_QUERY, "variables": {"id": node_id, "cursor": cursor}},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors for {legacy_id}: {payload['errors']}")

        node = payload["data"]["node"]
        if node is None:
            raise RuntimeError(f"No teacher found for legacy id {legacy_id}")

        if teacher is None:
            teacher = {k: v for k, v in node.items() if k != "ratings"}

        page = node["ratings"]
        ratings.extend(edge["node"] for edge in page["edges"])

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
        time.sleep(REQUEST_PAUSE)

    teacher["ratings"] = ratings
    return teacher


def format_review(index: int, r: dict) -> str:
    """Render a single review as a plain-text block."""
    lines = [f"--- Review {index} ---"]
    meta = [
        f"Class: {r.get('class') or 'N/A'}",
        f"Date: {(r.get('date') or '').split(' ')[0] or 'N/A'}",
        f"Quality: {r.get('qualityRating')}/5",
        f"Difficulty: {r.get('difficultyRatingRounded')}/5",
    ]
    would = r.get("wouldTakeAgain")
    if would is not None and would != -1:
        meta.append(f"Would take again: {'Yes' if would == 1 else 'No'}")
    grade = r.get("grade")
    if grade and grade != "Not sure yet":
        meta.append(f"Grade: {grade}")
    if r.get("isForOnlineClass"):
        meta.append("Online class: Yes")
    lines.append(" | ".join(meta))

    tags = (r.get("ratingTags") or "").replace("--", ", ").strip(", ")
    if tags:
        lines.append(f"Tags: {tags}")

    comment = (r.get("comment") or "").strip()
    lines.append(f"Comment: {comment if comment else '(no comment)'}")
    return "\n".join(lines)


def write_professor_file(prof: Professor, teacher: dict) -> Path:
    """Write one professor's reviews to a text file and return the path."""
    first = (teacher.get("firstName") or "").strip()
    last = (teacher.get("lastName") or "").strip()
    safe_last = (last or prof.legacy_id).replace(" ", "_")
    out_path = OUTPUT_DIR / f"{safe_last}_{prof.legacy_id}.txt"

    header = [
        f"Professor: {first} {last}".strip(),
        f"Department: {teacher.get('department') or 'N/A'}",
        f"School: {(teacher.get('school') or {}).get('name') or 'Purdue University'}",
        f"Course (from planning.md): {prof.course}",
        f"Overall quality: {teacher.get('avgRating')}/5",
        f"Average difficulty: {teacher.get('avgDifficulty')}/5",
        f"Would take again: {teacher.get('wouldTakeAgainPercent')}%",
        f"Total ratings: {teacher.get('numRatings')}",
        f"Source: https://www.ratemyprofessors.com/professor/{prof.legacy_id}",
        "",
        "=" * 60,
        "",
    ]

    reviews = teacher["ratings"]
    blocks = [format_review(i, r) for i, r in enumerate(reviews, start=1)]

    out_path.write_text("\n".join(header) + "\n\n".join(blocks) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_reviews = 0

    for prof in PROFESSORS:
        try:
            teacher = fetch_professor(prof.legacy_id)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"[FAIL] {prof.legacy_id} ({prof.course}): {exc}")
            continue

        path = write_professor_file(prof, teacher)
        n = len(teacher["ratings"])
        total_reviews += n
        name = f"{teacher.get('firstName', '')} {teacher.get('lastName', '')}".strip()
        print(f"[OK]   {name:<28} {n:>4} reviews -> {path.relative_to(Path.cwd())}")
        time.sleep(REQUEST_PAUSE)

    print(f"\nDone. Wrote {total_reviews} reviews across {len(PROFESSORS)} professors "
          f"into {OUTPUT_DIR.relative_to(Path.cwd())}/")


if __name__ == "__main__":
    main()

# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

My system covers the Purdue University core CS classes' professors. Students may want to get a better idea of what the Purdue CS department is like before applying or comitting to the university, and existing students may want to know what professors to take. Therefore, by making this knowledge (through rate my professor) accessible and digestable through a chatbot, students now have a comprehensive idea of what a certain class is like. Official descriptions don't go over teaching methodologies or professor's temperments and grading scales.

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

All sources are professor profiles on Rate My Professors (RMP) for the Purdue University
West Lafayette Computer Science department, scraped via RMP's GraphQL API. Each professor
page maps to a core CS course; together they cover the introductory sequence (CS 180/182)
through the systems core (CS 240/250/251/252). Source #1 is the department search listing
used to discover professors and is not scraped for review text.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RMP — Purdue CS department listing | Search/index page (not scraped for reviews) | https://www.ratemyprofessors.com/search/professors/783?q=*&did=11 |
| 2 | RMP — Jeff Turkstra (CS 240) | Student review page | https://www.ratemyprofessors.com/professor/2231495 |
| 3 | RMP — Marta Crowe (MGMT / CS 177) | Student review page | https://www.ratemyprofessors.com/professor/2120117 |
| 4 | RMP — Andres Posada (CS 251) | Student review page | https://www.ratemyprofessors.com/professor/2656983 |
| 5 | RMP — George Adams (CS 250) | Student review page | https://www.ratemyprofessors.com/professor/1931762 |
| 6 | RMP — Gustavo Rodriguez-Rivera (CS 252) | Student review page | https://www.ratemyprofessors.com/professor/132641 |
| 7 | RMP — Sarah Selke (CS 182) | Student review page | https://www.ratemyprofessors.com/professor/2931186 |
| 8 | RMP — Anthony Bergstrom (CS 180) | Student review page | https://www.ratemyprofessors.com/professor/2523519 |
| 9 | RMP — Hubert Dunsmore (CS 180, dept. head) | Student review page | https://www.ratemyprofessors.com/professor/2507062 |
| 10 | RMP — Wojciech Szpankowski (CS 182) | Student review page | https://www.ratemyprofessors.com/professor/132647 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 165 characters.

**Overlap:** 20 characters (the chunking window advances by 145 characters each step, so consecutive chunks share 20 characters).

**Why these choices fit your documents:** RMP reviews are short, free-form paragraphs, so a fixed character window is simpler and cheaper than token-based or semantic splitting. I started at 90 characters and iterated upward (90 -> 120 -> 150 -> 165): the smaller sizes fragmented reviews mid-word and mid-sentence, hurting both readability and embedding quality, while 165 captures roughly a full sentence's worth of context per chunk yet still keeps individual opinions isolated enough to retrieve distinct points. The 20-character overlap preserves context across boundaries so a phrase split between two chunks isn't lost entirely.

Preprocessing: reviews are scraped via RMP's GraphQL API into one plain-text file per professor (`documents/*.txt`), so there is no HTML to strip. The chunker parses each file and chunks only the free-text comment (everything after the `Comment:` flag); the file header and the per-review metadata line (class, date, quality/difficulty, etc.) are excluded from the chunk text. Instead, the professor name and the reviewer-stated class are captured as structured metadata and attached to every chunk for filtered retrieval. Reviews with no comment (or a literal "(no comment)") are dropped since there is nothing to embed.

**Final chunk count:** 1,863 chunks, produced from 861 reviews across 9 professors.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2`, loaded locally via the `sentence-transformers` library. It is a small, fast, CPU-friendly model that produces 384-dimensional embeddings, which keeps indexing and query latency low for a corpus of ~1,900 short review chunks. The same model embeds both the stored chunks and the incoming query, and ChromaDB compares them by cosine distance.

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

```
You are The Unofficial Guide, an assistant that answers questions about Purdue Computer Science professors and courses using student reviews from Rate My Professors.

Use only the information from the retrieved sources, do not use general information to respond to a user's prompt.

Guidelines:
- Base every claim on the numbered sources provided below. Cite the sources you rely on by their number, e.g. [1], [3].
- When sources name the professor or class, attribute opinions to them.
- Reviews can be subjective, satirical, or contradictory; reflect genuine disagreement rather than flattening it, and don't treat one review as fact.
- If the sources do not contain enough information to answer, say so plainly instead of guessing.
```

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Who generally teaches CS 180? | Dunsmore, Bergstrom, and sometimes Turkstra | Named Bergstrom, Turkstra, and Adams as CS 180 instructors; correctly noted the course is taught by different professors per section. | Partially relevant | Partially accurate |
| 2 | What are some common complaints about CS 240? | Turkstra's grading scale, length of homeworks | Identified the grading scale and heavy course structure/workload ("a nightmare", "absolute trash and torture"), while noting some dissenting positive reviews. | Relevant | Accurate |
| 3 | Who are some of the better-regarded professors? | Gustavo, Bergstrom, Dunsmore | Highlighted Gustavo Rodriguez-Rivera ("great/best/fantastic professor") and Marta Crowe as well-regarded; also surfaced a negative Turkstra review. | Partially relevant | Partially accurate |
| 4 | Who teaches CS 182? What are some grievances with them? | Selke and Szpankowski; both have complaints about their accents | Named both Szpankowski and Selke. Grievances: Selke "reads off slides"/disorganized; Szpankowski "hard to understand" but helpful one-on-one. | Relevant | Partially accurate |
| 5 | Who teaches CS 252, and what is the general consensus? | Gustavo Rodriguez-Rivera; generally positive | Named both Turkstra and Rodriguez-Rivera and reported a mixed consensus for each, rather than Gustavo's predominantly positive reception. | Relevant | Partially accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

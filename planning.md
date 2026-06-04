# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I am choosing the rate my professor page for the computer science department at Purdue. This knowledge is useful to students to give them an idea of how difficult the program might be, as well as how certain professors are regarded. The difficulty of professors and classes isn't available elsewhere, so these reviews can be used to give students intel on what classes and professors to take.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RMP  | List of profs  |https://www.ratemyprofessors.com/search/professors/783?q=*&did=11|
| 2 | RMP | CS 240 | https://www.ratemyprofessors.com/professor/2231495
| 3 | RMP | MGMT and 177 | https://www.ratemyprofessors.com/professor/2120117
| 4 | RMP | CS 251 | https://www.ratemyprofessors.com/professor/2656983
| 5 | RMP | CS 250 | https://www.ratemyprofessors.com/professor/1931762
| 6 | RMP | CS 252 | https://www.ratemyprofessors.com/professor/132641
| 7 | RMP | CS 182 | https://www.ratemyprofessors.com/professor/2931186
| 8 | RMP | CS 180 | https://www.ratemyprofessors.com/professor/2523519
| 9 | RMP | Dep head, 180 | https://www.ratemyprofessors.com/professor/2507062
| 10 | RMP | CS 182 | https://www.ratemyprofessors.com/professor/132647

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

Chunking can be done by a certain amount of characters since reviews are generally short paragraphs. For instance, we can start at 190 characters ber chunk. 

**Overlap:**

A 20 or so character overlap might be good, since that should clear any possible lost context.

**Reasoning:**

Reviews are generally short paragraph, and sentences are not too long. Hence, we can use a set amoutn of characters per chunk to save time and compute.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

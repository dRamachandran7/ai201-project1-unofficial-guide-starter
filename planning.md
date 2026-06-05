# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
I am choosing the rate my professor page for the computer science department at Purdue. This knowledge is useful to students to give them an idea of how difficult the program might be, as well as how certain professors are regarded. The difficulty of professors and classes isn't available elsewhere, so these reviews can be used to give students intel on what classes and professors to take. Specifically, this is meant to guide students through the core cs classes and their professors.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | RMP  | List of profs  |https://www.ratemyprofessors.com/search/professors/783?q=*&did=11 |
| 2 | RMP | CS 240 | https://www.ratemyprofessors.com/professor/2231495 |
| 3 | RMP | MGMT and 177 | https://www.ratemyprofessors.com/professor/2120117 |
| 4 | RMP | CS 251 | https://www.ratemyprofessors.com/professor/2656983 |
| 5 | RMP | CS 250 | https://www.ratemyprofessors.com/professor/1931762 |
| 6 | RMP | CS 252 | https://www.ratemyprofessors.com/professor/132641 |
| 7 | RMP | CS 182 | https://www.ratemyprofessors.com/professor/2931186 |
| 8 | RMP | CS 180 | https://www.ratemyprofessors.com/professor/2523519 |
| 9 | RMP | Dep head, 180 | https://www.ratemyprofessors.com/professor/2507062 |
| 10 | RMP | CS 182 | https://www.ratemyprofessors.com/professor/132647 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

Chunking can be done by a certain amount of characters since reviews are generally short paragraphs. For instance, we can start at 120 characters ber chunk. However, we should make sure to only start that chunking after the 'Comment:' flag and parse the prof and class as metadata separately. 

**Overlap:**

A 20 or so character overlap might be good, since that should clear any possible lost context.

**Reasoning:**

Reviews are generally short paragraph, and sentences are not too long. Hence, we can use a set amoutn of characters per chunk to save time and compute. By chunking each review slightly smaller, we can also isolate certain opinions and ideas better.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

We will be using the all-MiniLM-L6-v2 via sentence-transformers model to embed. 

**Top-k:**

Seeing as there are not many professors for each course, a top-k of 3 would be a good starting point. This would allow for multiple profs who teach the same class to be addressed, as well as the full list of profs in the department. 

**Production tradeoff reflection:**

We might want to make sure we have more space for storing context, so that the llm would be able to hold a conversation, as opposed to just answering questions.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Who generally teaches CS 180? | Dunsmore, Bergstrom, and sometimes Turkstra. |
| 2 | What are some common complaints about CS 240? | Turkstra's grading scale, length of homeworks |
| 3 | Who are some of the better-regarded professors? | Gustavo, Bergstrom, Dunsmore |
| 4 | Who teaches CS 182? What are some greivances with them? | CS 182 is generally taught by Selke and Szpankowski. Both have complaints about their accents. |
| 5 | Who teaches CS 252, and what is the general consensus on them? | CS 252 is generally taught by Gustavo Rodriguez-Rivera, and he has generally positive reviews. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. There are quite a few satirical reviews on the site which an llm may not be able to recognize as satire, and may use as legitamite information. Therefore, it may produce some unexpected and incorrect responses.

2. In addition to satirical reviews, there are also very short ones. These chunks might throw off the chunking splits, and lead to some information being lost.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

Ingestion: Web scraping script that scrapes reviews and key info as plain text -> Chunking: python code to create 90 character chunks -> Embedding: sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2') to create embeddings for each chunk -> Vector store: ChromaDB, using collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas) to add embeddings from previous step into vector DB. Can collect the professors and classes as metadata to be used for filtering in the next step -> Generation: groq, 

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

Example chunks (metadata at top):

[Turkstra_2231495_r27_c2]  prof=Jeff Turkstra  class=CS240  len=56
'ciate everything about this class and his teaching style'

[Turkstra_2231495_r162_c2]  prof=Jeff Turkstra  class=CS252  len=75
's. Sent several people I know to CAPS for breakdowns because of the course.'

[Szpankowski_132647_r31_c2]  prof=Wojciech Szpankowski  class=CS110  len=77
'teacher even beside these things, but he knows the material _extremely_ well.'

[Crowe_2120117_r12_c2]  prof=Marta Crowe  class=CS235  len=79
"s a professor, you'll do well. Just make sure to do the work and ask questions."

[Turkstra_2231495_r100_c1]  prof=Jeff Turkstra  class=CS307  len=150
"ut isn't afraid to take away points unnecessarily (for us, it was a simple submission error). I can see why some people don't like him but you will be"


**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

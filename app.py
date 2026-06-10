"""Minimal Gradio web UI for The Unofficial Guide.

A single-input chat-style interface over the full RAG pipeline:
    question -> entity extraction + filtered retrieval -> grounded Groq answer
with the cited source reviews shown beneath the answer.

Run:  python app.py   (then open the printed local URL)
"""

from __future__ import annotations

import gradio as gr

from generate import generate_answer

EXAMPLES = [
    "Who generally teaches CS 180?",
    "What are some common complaints about CS 240?",
    "Who teaches CS 252, and what is the general consensus on them?",
    "Is Turkstra a good professor?",
]


def answer_question(query: str) -> tuple[str, str]:
    """Run a query through the pipeline; return (answer, sources markdown)."""
    query = (query or "").strip()
    if not query:
        return "Please enter a question.", ""
    result = generate_answer(query)
    return result["answer"], result["citations"]


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about Purdue CS professors and courses. Answers are grounded only "
        "in student reviews from Rate My Professors."
    )
    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. What are common complaints about CS 240?",
        lines=2,
    )
    ask = gr.Button("Ask", variant="primary")
    answer = gr.Markdown(label="Answer")
    sources = gr.Markdown(label="Sources")

    gr.Examples(examples=EXAMPLES, inputs=question)

    ask.click(answer_question, inputs=question, outputs=[answer, sources])
    question.submit(answer_question, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()

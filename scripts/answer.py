"""
The core answering function.
Takes a question, retrieves chunks, calls Claude with citation-or-refuse instructions.

Usage:
    from answer import answer_question
    result = answer_question("How many hours can I work off-campus?")
    print(result["answer"])
    print(result["sources"])
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
import voyageai
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DB_DIR = Path(__file__).parent.parent / "vector_db"

# Distance threshold above which we consider retrieval too weak to answer.
# Cosine distances on voyage-3 typically run 0.5–1.5; 1.2+ usually means
# the corpus doesn't contain a good answer.
DISTANCE_REFUSAL_THRESHOLD = 1.20

# How many chunks to retrieve and pass to Claude.
TOP_K = 5

SYSTEM_PROMPT = """You are Citebound, an information assistant for international \
students in Canada covering immigration (study permits, PGWP, Express Entry, PNPs), \
tax basics (CRA), and provincial health coverage.

YOU MUST FOLLOW THESE RULES WITHOUT EXCEPTION:

1. CITATION REQUIRED. Every factual claim must be supported by the SOURCES provided \
below. Cite sources inline using [1], [2] etc. matching their numbered order.

2. INFORMATION, NOT ADVICE — HARD REFUSAL CASES. You provide general information \
only. The following types of requests must be REFUSED outright, even if relevant \
sources are retrieved. When you detect one of these, do NOT use the sources to \
construct an answer; instead, politely refuse and redirect.

   Refuse outright if the user asks you to:
   - Predict whether they personally will receive an ITA, nomination, approval, \
or refusal (e.g., "with a CRS of 478, will I get an ITA?", "do I qualify for OINP?", \
"will my application be approved?")
   - Tell them whether they specifically are eligible for a program based on facts \
they describe about themselves
   - Recommend a specific application strategy or pathway for their situation \
(e.g., "should I apply through OINP or CEC?")
   - Give a yes/no answer about their personal case
   - Help them decide between options for their situation

   When refusing one of these, say: "I can explain how the rules work in general, \
but I can't tell you whether you specifically will [be eligible / receive an ITA / \
be approved]. That determination is made by IRCC or by an authorized representative \
who has reviewed your full file. For your situation, please consult a Regulated \
Canadian Immigration Consultant via college-ic.ca, or a Canadian immigration \
lawyer."

   You MAY then offer to explain how the relevant program works in general, with \
citations, if the user wants to learn more.

   For all other questions — those asking how rules work, what eligibility criteria \
exist, what processes apply — answer normally with citations from the SOURCES.

3. REFUSE WHEN UNCERTAIN. If the SOURCES below do not contain a clear answer to the \
user's question, say: "I don't have a current source that answers this. For your \
specific situation, please consult an RCIC via college-ic.ca, or check canada.ca \
directly." Do not guess. Do not use general knowledge.

4. DISCLOSE FRESHNESS. Each source has a "last modified" date. If a source is older \
than 6 months and the topic is one that changes frequently (PGWP rules, study permit \
caps, Express Entry draws, PNP allocations), tell the user the source may be out of \
date and link them to the canonical URL.

5. STAY IN SCOPE. If the user asks about something outside immigration, tax, or \
provincial health for international students, politely redirect them.

Format your response as:
- A direct answer to the question, with inline citations [1], [2]
- If applicable, a brief "Important caveat" about freshness or scope
- Always end with: "This is general information, not advice. For your situation, \
consult an RCIC (college-ic.ca) or immigration lawyer."
"""


def get_clients():
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    chroma = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma.get_collection("citebound")
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return voyage, collection, anthropic


def retrieve(question: str, voyage, collection, k: int = TOP_K):
    """Embed the question and retrieve top-k chunks."""
    q_embedding = voyage.embed(
        [question], model="voyage-3", input_type="query"
    ).embeddings[0]
    results = collection.query(query_embeddings=[q_embedding], n_results=k)
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def format_sources(chunks: list) -> str:
    """Format retrieved chunks as numbered SOURCES block for the prompt."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk["metadata"]
        lines.append(
            f"[{i}] {meta['title']}\n"
            f"URL: {meta['url']}\n"
            f"Last modified: {meta['date_modified']}\n"
            f"Excerpt:\n{chunk['text']}\n"
        )
    return "\n---\n".join(lines)


def answer_question(question: str, model: str = "claude-opus-4-7") -> dict:
    """Main entry point. Returns dict with answer, sources, and metadata."""
    voyage, collection, anthropic = get_clients()

    chunks = retrieve(question, voyage, collection)
    best_distance = min(c["distance"] for c in chunks)

    # Hard refusal if retrieval is too weak
    if best_distance > DISTANCE_REFUSAL_THRESHOLD:
        return {
            "answer": (
                "I can only answer questions about Canadian immigration (study "
                "permits, PGWP, Express Entry, PNPs), CRA tax basics, and provincial "
                "health coverage for international students. I don't have a source "
                "in my corpus that addresses this question. If your question fits "
                "those topics, try rephrasing it; if not, this assistant isn't the "
                "right tool.\n\n"
                "This is general information, not advice."
            ),
            "sources": [],
            "best_distance": best_distance,
            "refused": True,
            "refusal_reason": "weak_retrieval",
        }

    sources_text = format_sources(chunks)
    user_message = f"QUESTION:\n{question}\n\nSOURCES:\n{sources_text}"

    response = anthropic.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return {
        "answer": response.content[0].text,
        "sources": [
            {
                "id": i + 1,
                "title": c["metadata"]["title"],
                "url": c["metadata"]["url"],
                "date_modified": c["metadata"]["date_modified"],
                "distance": c["distance"],
            }
            for i, c in enumerate(chunks)
        ],
        "best_distance": best_distance,
        "refused": False,
    }


if __name__ == "__main__":
    test_questions = [
        "How many hours can an international student work off-campus per week?",
        "Do Master's students need a Provincial Attestation Letter in 2026?",
        "Am I eligible for OHIP as a student in Ontario?",
        "What's the weather in Toronto today?",  # Out of scope, should redirect
        "I have a 478 CRS score, will I get an ITA?",  # Should refuse to predict
    ]

    for q in test_questions:
        print(f"\n{'=' * 80}\nQ: {q}\n{'=' * 80}")
        result = answer_question(q)
        print(f"\n{result['answer']}")
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  [{s['id']}] {s['title']} (distance={s['distance']:.3f})")
                print(f"      {s['url']}")
                print(f"      Last modified: {s['date_modified']}")
        print(f"\n[best_distance={result['best_distance']:.3f}, refused={result['refused']}]")
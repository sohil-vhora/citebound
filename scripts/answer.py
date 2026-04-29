"""
The core answering function.
Takes a question, retrieves chunks, calls Claude with citation-or-refuse instructions.

Usage:
    from answer import answer_question
    result = answer_question("How many hours can I work off-campus?")
    print(result["answer"])
    print(result["sources"])

    # With conversation history:
    result = answer_question(
        "yes it was paid to Seneca",
        history=[
            {"role": "user", "content": "Can I claim foreign tuition credits?"},
            {"role": "assistant", "content": "..."},
        ],
    )
"""

import os
from pathlib import Path

import chromadb
import voyageai
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
DB_DIR = Path(__file__).parent.parent / "vector_db"

# Distance threshold above which we consider retrieval too weak to answer.
# Cosine distances on voyage-3 typically run 0.5–1.5; 1.2+ usually means
# the corpus doesn't contain a good answer.
DISTANCE_REFUSAL_THRESHOLD = 1.20

# How many chunks to retrieve and pass to Claude.
TOP_K = 5

# Models
ANSWER_MODEL = "claude-opus-4-7"
REWRITE_MODEL = "claude-haiku-4-5-20251001"  # cheap, fast for query rewriting

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


# ─────────────────────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────────────────────
def get_clients():
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    chroma = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma.get_collection("citebound")
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return voyage, collection, anthropic


# ─────────────────────────────────────────────────────────────
# Query rewriting
# ─────────────────────────────────────────────────────────────
def rewrite_followup_to_standalone(
    question: str,
    history: list,
    anthropic,
) -> str:
    """
    Given a follow-up question and prior conversation, rewrite the question
    into a standalone query suitable for retrieval.

    If there's no history, returns the question unchanged.
    """
    if not history:
        return question

    # Build a compact history string from the last 2 turns
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content'][:500]}"
        for m in history[-4:]
    )

    rewrite_prompt = f"""Given the conversation history below, rewrite the user's \
latest question as a STANDALONE search query that captures full context. The \
rewritten query will be used for vector search over Canadian government \
documents, so it should contain the key concepts and terms.

If the latest question already stands alone (e.g., it's a fresh new topic), \
return it as-is.

Conversation history:
{history_text}

User's latest message: {question}

Output ONLY the rewritten standalone query, nothing else. No preamble, no \
explanation."""

    response = anthropic.messages.create(
        model=REWRITE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": rewrite_prompt}],
    )
    rewritten = response.content[0].text.strip()
    return rewritten


# ─────────────────────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────────────────────
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
    """Format retrieved chunks as a numbered SOURCES block for the prompt."""
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


# ─────────────────────────────────────────────────────────────
# Refusal messages
# ─────────────────────────────────────────────────────────────
def _weak_retrieval_refusal(search_query: str, has_history: bool) -> str:
    """Different message depending on whether this is a follow-up or fresh question."""
    if has_history:
        return (
            f"I understood your follow-up as:\n\n_\"{search_query}\"_\n\n"
            "I don't have a source in my corpus that directly addresses this. "
            "This often happens when a question touches on rules I haven't "
            "indexed yet (for example, tuition credit carryforward across a "
            "change in tax residency, which is a CRA topic outside my current "
            "scope). For an authoritative answer, please check the CRA "
            "directly or consult a Canadian tax professional. For immigration "
            "matters, an RCIC (college-ic.ca) is the right resource.\n\n"
            "This is general information, not advice."
        )
    return (
        "I can only answer questions about Canadian immigration (study "
        "permits, PGWP, Express Entry, PNPs), CRA tax basics, and provincial "
        "health coverage for international students. I don't have a source "
        "in my corpus that addresses this question. If your question fits "
        "those topics, try rephrasing it; if not, this assistant isn't the "
        "right tool.\n\n"
        "This is general information, not advice."
    )


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────
def answer_question(
    question: str,
    history: list = None,
    model: str = ANSWER_MODEL,
) -> dict:
    """
    Args:
        question: the user's current question
        history: list of prior {"role", "content"} messages (optional)
        model: Claude model to use for the final answer

    Returns dict with answer, sources, and metadata.
    """
    history = history or []
    voyage, collection, anthropic = get_clients()

    # Rewrite follow-ups into standalone queries for better retrieval
    search_query = rewrite_followup_to_standalone(question, history, anthropic)

    chunks = retrieve(search_query, voyage, collection)
    best_distance = min(c["distance"] for c in chunks)

    # Hard refusal if retrieval is too weak
    if best_distance > DISTANCE_REFUSAL_THRESHOLD:
        return {
            "answer": _weak_retrieval_refusal(search_query, has_history=bool(history)),
            "sources": [],
            "best_distance": best_distance,
            "refused": True,
            "refusal_reason": "weak_retrieval",
            "search_query_used": search_query,
        }

    sources_text = format_sources(chunks)
    user_message = f"QUESTION:\n{question}\n\nSOURCES:\n{sources_text}"

    # Build messages: include prior history so Claude knows the conversation context
    messages = []
    for m in history[-6:]:  # cap history depth for token budget
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    response = anthropic.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=messages,
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
        "search_query_used": search_query,
    }


# ─────────────────────────────────────────────────────────────
# Manual test harness
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_questions = [
        "How many hours can an international student work off-campus per week?",
        "Do Master's students need a Provincial Attestation Letter in 2026?",
        "How does the GST/HST credit work for international students?",
        "Am I eligible for OHIP as a student in Ontario?",
        "What's the financial requirement for a study permit?",
        "How do I extend my study permit before it expires?",
        "Are co-op work permits still required after April 2026?",
        "How does Quebec's CAQ differ from a PAL?",
        "Can a Master's student in BC get MSP?",
        "Do Alberta students get AHCIP?",
        "What's the TFSA contribution rule for non-residents?",
        "How long are biometrics valid for?",
        "What replaced PEQ in Quebec?",
        "I have a 478 CRS score, will I get an ITA?",
        "What's the weather in Toronto?",
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
        print(
            f"\n[best_distance={result['best_distance']:.3f}, "
            f"refused={result['refused']}, "
            f"search_query='{result.get('search_query_used', q)}']"
        )
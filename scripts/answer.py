"""
The core answering function.
Two-layer refusal architecture:
1. Heuristic detector for personal-prediction questions ("will I get", "am I
   eligible") — these route to the LLM with refusal-first framing regardless
   of retrieval confidence.
2. Distance threshold for off-corpus questions — if retrieval is too weak,
   we refuse honestly rather than letting the LLM hallucinate.

Backend selection:
- Local: uses persistent ChromaDB if vector_db/ exists.
- Cloud: builds an in-memory FAISS index from corpus/ JSONs.
  FAISS is used on cloud because ChromaDB's in-memory mode doesn't
  survive Streamlit reruns reliably.
"""

import os
from pathlib import Path

import chromadb
import voyageai
from anthropic import Anthropic
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
DB_DIR = Path(__file__).parent.parent / "vector_db"
DISTANCE_REFUSAL_THRESHOLD = 1.20
TOP_K = 5
ANSWER_MODEL = "claude-opus-4-7"
REWRITE_MODEL = "claude-haiku-4-5-20251001"

# ─────────────────────────────────────────────────────────────
# Personal-prediction heuristic
# ─────────────────────────────────────────────────────────────
PERSONAL_PREDICTION_PATTERNS = [
    "will i get", "will i be", "will my application",
    "am i eligible", "do i qualify", "do i meet",
    "should i apply", "what are my chances",
    "what's my chance", "what is my chance",
    "would i qualify", "would i be eligible",
]


def looks_like_personal_prediction(question: str) -> bool:
    q = question.lower().strip()
    return any(p in q for p in PERSONAL_PREDICTION_PATTERNS)


# ─────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Citebound, an information assistant for international \
students in Canada covering immigration (study permits, PGWP, Express Entry, PNPs), \
tax basics (CRA), and provincial health coverage.

YOU MUST FOLLOW THESE RULES WITHOUT EXCEPTION:

1. CITATION REQUIRED. Every factual claim must be supported by the SOURCES provided \
below. Cite sources inline using [1], [2] etc. matching their numbered order.

2. INFORMATION, NOT ADVICE — HARD REFUSAL CASES. You provide general information \
only. The following types of requests must be REFUSED outright, even if relevant \
sources are retrieved.

   Refuse outright if the user asks you to:
   - Predict whether they personally will receive an ITA, nomination, approval, or refusal
   - Tell them whether they specifically are eligible for a program based on facts they describe
   - Recommend a specific application strategy or pathway for their situation
   - Give a yes/no answer about their personal case
   - Help them decide between options for their situation

   When refusing one of these, say: "I can explain how the rules work in general, \
but I can't tell you whether you specifically will [be eligible / receive an ITA / \
be approved]. That determination is made by IRCC or by an authorized representative \
who has reviewed your full file. For your situation, please consult a Regulated \
Canadian Immigration Consultant via college-ic.ca, or a Canadian immigration \
lawyer."

   You MAY then offer to explain how the relevant program works in general, with citations.

3. REFUSE WHEN UNCERTAIN. If the SOURCES below do not contain a clear answer, say: \
"I don't have a current source that answers this. For your specific situation, \
please consult an RCIC via college-ic.ca, or check canada.ca directly." Do not \
guess. Do not use general knowledge.

4. DISCLOSE FRESHNESS. Each source has a "last modified" date. If older than 6 \
months on a high-volatility topic (PGWP, study permit caps, Express Entry draws, \
PNP allocations), tell the user the source may be out of date and link to the \
canonical URL.

5. STAY IN SCOPE. Outside immigration, tax, or provincial health for international \
students, politely redirect.

Format your response as:
- A direct answer with inline citations [1], [2]
- A brief "Important caveat" if applicable
- Always end with: "This is general information, not advice. For your situation, \
consult an RCIC (college-ic.ca) or immigration lawyer."
"""


# ─────────────────────────────────────────────────────────────
# Index builder (cached across Streamlit reruns)
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Building vector index... (one-time, ~30s)")
def _build_index():
    """
    Returns one of two shapes:
    - {"backend": "chroma", "collection": <Chroma collection>}
    - {"backend": "faiss", "index": <FAISS index>, "texts": [...], "metadatas": [...]}

    retrieve() handles both shapes.
    """
    import json

    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

    # ─── Local path: persistent Chroma ────────────────────────
    if (DB_DIR / "chroma.sqlite3").exists():
        try:
            chroma = chromadb.PersistentClient(path=str(DB_DIR))
            collection = chroma.get_collection("citebound")
            return {"backend": "chroma", "collection": collection}
        except Exception:
            pass  # fall through to FAISS

    # ─── Cloud path: build FAISS in-memory ────────────────────
    import faiss
    import numpy as np
    import tiktoken

    tokenizer = tiktoken.get_encoding("cl100k_base")
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 50

    def clean_text(text):
        replacements = {
            "â€™": "'", "â€œ": '"', "â€\x9d": '"',
            "â€“": "-", "â€”": "—", "Â ": " ", "\xa0": " ",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text

    def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
        tokens = tokenizer.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunks.append(tokenizer.decode(tokens[start:end]))
            if end == len(tokens):
                break
            start = end - overlap
        return chunks

    corpus_dir = Path(__file__).parent.parent / "corpus"
    docs = []
    for path in sorted(corpus_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            docs.append(json.load(f))

    all_texts = []
    all_metadatas = []
    for doc in docs:
        cleaned = clean_text(doc["content"])
        chunks = chunk_text(cleaned)
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadatas.append({
                "source_id": doc["id"],
                "url": doc["url"],
                "title": doc["title"],
                "topic": doc["topic"],
                "date_modified": doc.get("date_modified") or "unknown",
                "chunk_index": i,
            })

    # Embed in batches
    BATCH = 64
    embeddings = []
    for i in range(0, len(all_texts), BATCH):
        batch = all_texts[i:i + BATCH]
        result = voyage.embed(batch, model="voyage-3", input_type="document")
        embeddings.extend(result.embeddings)

    embeddings_array = np.array(embeddings, dtype="float32")
    # Normalize for cosine similarity (FAISS inner product on normalized vectors = cosine sim)
    faiss.normalize_L2(embeddings_array)
    index = faiss.IndexFlatIP(embeddings_array.shape[1])
    index.add(embeddings_array)

    return {
        "backend": "faiss",
        "index": index,
        "texts": all_texts,
        "metadatas": all_metadatas,
    }


def get_clients():
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    index_handle = _build_index()
    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return voyage, index_handle, anthropic


# ─────────────────────────────────────────────────────────────
# Query rewriting
# ─────────────────────────────────────────────────────────────
def rewrite_followup_to_standalone(question, history, anthropic):
    if not history:
        return question

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

Output ONLY the rewritten standalone query, nothing else."""

    response = anthropic.messages.create(
        model=REWRITE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": rewrite_prompt}],
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────
# Retrieval (backend-agnostic)
# ─────────────────────────────────────────────────────────────
def retrieve(question, voyage, index_handle, k=TOP_K):
    q_embedding = voyage.embed(
        [question], model="voyage-3", input_type="query"
    ).embeddings[0]

    if index_handle["backend"] == "chroma":
        collection = index_handle["collection"]
        results = collection.query(query_embeddings=[q_embedding], n_results=k)
        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return chunks

    # FAISS path
    import numpy as np
    import faiss
    q_array = np.array([q_embedding], dtype="float32")
    faiss.normalize_L2(q_array)
    similarities, indices = index_handle["index"].search(q_array, k)

    chunks = []
    for i, idx in enumerate(indices[0]):
        # Convert cosine similarity to a distance comparable to Chroma's range
        similarity = float(similarities[0][i])
        distance = (1.0 - similarity) * 2.0  # rough scale to 0-2 range
        chunks.append({
            "text": index_handle["texts"][idx],
            "metadata": index_handle["metadatas"][idx],
            "distance": distance,
        })
    return chunks


def format_sources(chunks):
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
def _weak_retrieval_refusal(search_query, has_history):
    if has_history:
        return (
            f"I understood your follow-up as:\n\n_\"{search_query}\"_\n\n"
            "I don't have a source in my corpus that directly addresses this. "
            "This often happens when a question touches on rules I haven't "
            "indexed yet. For an authoritative answer, please check canada.ca "
            "directly or consult an RCIC via college-ic.ca.\n\n"
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
# LLM helpers
# ─────────────────────────────────────────────────────────────
def _call_llm_with_chunks(question, chunks, history, anthropic, model, extra_instruction=""):
    sources_text = format_sources(chunks)
    user_message = f"QUESTION{extra_instruction}:\n{question}\n\nSOURCES:\n{sources_text}"

    messages = []
    for m in history[-6:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    response = anthropic.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def _format_sources_response(chunks):
    return [
        {
            "id": i + 1,
            "title": c["metadata"]["title"],
            "url": c["metadata"]["url"],
            "date_modified": c["metadata"]["date_modified"],
            "distance": c["distance"],
        }
        for i, c in enumerate(chunks)
    ]


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────
def answer_question(question, history=None, model=ANSWER_MODEL):
    history = history or []
    voyage, index_handle, anthropic = get_clients()

    search_query = rewrite_followup_to_standalone(question, history, anthropic)
    chunks = retrieve(search_query, voyage, index_handle)
    best_distance = min(c["distance"] for c in chunks)

    # ─── Layer 1: Personal-prediction questions ────────────────
    if looks_like_personal_prediction(question):
        answer_text = _call_llm_with_chunks(
            question, chunks, history, anthropic, model,
            extra_instruction=" (personal-prediction — refuse per Rule 2 first, then optionally explain in general)",
        )
        return {
            "answer": answer_text,
            "sources": _format_sources_response(chunks),
            "best_distance": best_distance,
            "refused": True,
            "refusal_reason": "personal_prediction",
            "search_query_used": search_query,
            "routed_as": "personal_prediction",
        }

    # ─── Layer 2: Weak retrieval ───────────────────────────────
    if best_distance > DISTANCE_REFUSAL_THRESHOLD:
        return {
            "answer": _weak_retrieval_refusal(search_query, has_history=bool(history)),
            "sources": [],
            "best_distance": best_distance,
            "refused": True,
            "refusal_reason": "weak_retrieval",
            "search_query_used": search_query,
            "routed_as": "weak_retrieval_refusal",
        }

    # ─── Default path ──────────────────────────────────────────
    answer_text = _call_llm_with_chunks(question, chunks, history, anthropic, model)
    return {
        "answer": answer_text,
        "sources": _format_sources_response(chunks),
        "best_distance": best_distance,
        "refused": False,
        "refusal_reason": None,
        "search_query_used": search_query,
        "routed_as": "standard",
    }


if __name__ == "__main__":
    # Quick sanity check when run directly
    test_questions = [
        "How many hours can I work off-campus per week?",
        "I have a CRS of 478, will I get an ITA?",
        "What's the weather in Toronto?",
    ]
    for q in test_questions:
        print(f"\n=== {q} ===")
        r = answer_question(q)
        print(r["answer"][:500])
        print(f"[routed_as={r['routed_as']}, refused={r['refused']}]")
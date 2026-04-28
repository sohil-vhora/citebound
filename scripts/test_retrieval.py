"""
Quick sanity check on the vector store. Asks 5 questions, prints top 3 chunks per question.

Run from project root: python scripts/test_retrieval.py
"""

import os
from pathlib import Path

import chromadb
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_DIR = Path(__file__).parent.parent / "vector_db"

QUESTIONS = [
    # Original 5
    "How many hours can an international student work off-campus per week?",
    "Do Master's students need a Provincial Attestation Letter in 2026?",
    "How does the GST/HST credit work for international students?",
    "Am I eligible for OHIP as a student in Ontario?",
    "What's the deadline for an OINP Masters Graduate stream application?",

    # New questions probing the expanded corpus
    "What's the financial requirement for a study permit?",
    "How do I extend my study permit before it expires?",
    "Are co-op work permits still required after April 2026?",
    "How does Quebec's CAQ differ from a PAL?",
    "What's the Express Entry STEM category?",
    "Can a Master's student in BC get MSP?",
    "Do Alberta students get AHCIP?",
    "What's the TFSA contribution rule for non-residents?",
    "How long are biometrics valid for?",
    "What replaced PEQ in Quebec?",
]


def main():
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    chroma = chromadb.PersistentClient(path=str(DB_DIR))
    collection = chroma.get_collection("citebound")

    for q in QUESTIONS:
        print(f"\n{'=' * 80}\nQ: {q}\n{'=' * 80}")
        q_embedding = voyage.embed([q], model="voyage-3", input_type="query").embeddings[0]
        results = collection.query(query_embeddings=[q_embedding], n_results=3)

        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            text = results["documents"][0][i]
            distance = results["distances"][0][i]
            print(f"\n[{i + 1}] {meta['source_id']} (distance={distance:.3f})")
            print(f"    URL: {meta['url']}")
            print(f"    Text: {text[:300]}...")


if __name__ == "__main__":
    main()
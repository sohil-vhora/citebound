"""
Read corpus JSONs, split into ~400-token chunks with overlap,
embed each chunk, and store in a local Chroma vector database.

Run from project root: python scripts/chunk_and_embed.py
"""

import json
import os
from pathlib import Path

import chromadb
import tiktoken
import voyageai
from dotenv import load_dotenv

load_dotenv()

CORPUS_DIR = Path(__file__).parent.parent / "corpus"
DB_DIR = Path(__file__).parent.parent / "vector_db"
DB_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 400      # tokens
CHUNK_OVERLAP = 50    # tokens
EMBED_MODEL = "voyage-3"

# Tokenizer used to count tokens. cl100k_base is OpenAI's GPT-4 tokenizer —
# we just use it as a generic token counter; Voyage uses its own internally.
tokenizer = tiktoken.get_encoding("cl100k_base")


def clean_text(text: str) -> str:
    """Fix common encoding artifacts from canada.ca scrapes."""
    replacements = {
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€“": "-",
        "â€”": "—",
        "Â ": " ",
        "\xa0": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks measured in tokens."""
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start = end - overlap
    return chunks


def main():
    # Load all corpus documents
    docs = []
    for path in sorted(CORPUS_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            docs.append(json.load(f))
    print(f"Loaded {len(docs)} documents from {CORPUS_DIR}")

    # Set up Voyage client
    voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

    # Set up Chroma client (persistent — saves to disk)
    chroma = chromadb.PersistentClient(path=str(DB_DIR))
    # Recreate the collection from scratch so re-running is clean
    if "citebound" in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection("citebound")
    collection = chroma.create_collection(name="citebound")

    all_chunks = []
    for doc in docs:
        cleaned = clean_text(doc["content"])
        chunks = chunk_text(cleaned)
        print(f"  {doc['id']}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{doc['id']}__{i:03d}",
                "text": chunk,
                "metadata": {
                    "source_id": doc["id"],
                    "url": doc["url"],
                    "title": doc["title"],
                    "topic": doc["topic"],
                    "date_modified": doc.get("date_modified") or "unknown",
                    "chunk_index": i,
                },
            })

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Embedding with {EMBED_MODEL}...")

    # Embed in batches (Voyage allows up to 128 texts per call)
    BATCH = 64
    embeddings = []
    texts = [c["text"] for c in all_chunks]
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        result = voyage.embed(batch, model=EMBED_MODEL, input_type="document")
        embeddings.extend(result.embeddings)
        print(f"  embedded {min(i + BATCH, len(texts))}/{len(texts)}")

    # Store in Chroma
    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c["metadata"] for c in all_chunks],
    )

    print(f"\nStored {len(all_chunks)} chunks in Chroma at {DB_DIR}")
    print(f"Collection size: {collection.count()}")


if __name__ == "__main__":
    main()
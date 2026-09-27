import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
QDRANT_PATH = BASE_DIR / "qdrant_data"
COLLECTION_NAME = "dental_knowledge"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

if not QDRANT_PATH.exists():
    print("Error: Qdrant database directory not found. Please run ingest.py first!")
    exit(1)

print("Loading model and connecting to vector database...")
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
client = QdrantClient(path=str(QDRANT_PATH))

try:
    question = input("\nAsk a clinical question: ").strip()

    if not question:
        print("No query entered. Exiting.")
    else:
        print("\nSearching knowledge base...\n")

        query_vector = model.encode(
            question,
            normalize_embeddings=True,
        ).tolist()

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=3,
            with_payload=True,
        ).points

        if not results:
            print("No matching documents found.")
        else:
            for i, result in enumerate(results, start=1):
                print("=" * 60)
                print(f"Result {i} (Similarity Score: {result.score:.4f})")
                print(f"File: {result.payload.get('filename', 'Unknown')}")
                print("-" * 60)
                print(result.payload.get("text", ""))
            print("=" * 60)
finally:
    client.close()

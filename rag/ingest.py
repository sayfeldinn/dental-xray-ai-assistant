from pathlib import Path
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
QDRANT_PATH = BASE_DIR / "qdrant_data"
COLLECTION_NAME = "dental_knowledge"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("---------------------------------")
print("RAG Ingestion Pipeline")
print("---------------------------------")

if not DOCUMENTS_DIR.exists():
    print(f"Error: Documents directory '{DOCUMENTS_DIR}' does not exist.")
    print("Please run convert.py first!")
    exit(1)

# Read documents
doc_files = list(DOCUMENTS_DIR.glob("*.txt"))
if not doc_files:
    print(f"Error: No .txt files found in '{DOCUMENTS_DIR}'.")
    print("Please run convert.py first!")
    exit(1)

documents = []
for file_path in doc_files:
    text = file_path.read_text(encoding="utf-8").strip()
    if text:
        documents.append({
            "filename": file_path.name,
            "text": text,
        })

print(f"Found {len(documents)} documents in '{DOCUMENTS_DIR.name}/'.")

# Load embedding model
print(f"Loading embedding model ({EMBEDDING_MODEL_NAME})...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Get vector size dynamically
test_vector = embedding_model.encode("test")
VECTOR_SIZE = len(test_vector)
print(f"Vector dimension size: {VECTOR_SIZE}")

# Initialize Qdrant Client
print(f"Opening Qdrant database at '{QDRANT_PATH.name}/'...")
client = QdrantClient(path=str(QDRANT_PATH))

# Recreate collection
if client.collection_exists(COLLECTION_NAME):
    print(f"Deleting existing collection '{COLLECTION_NAME}'...")
    client.delete_collection(COLLECTION_NAME)

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(
        size=VECTOR_SIZE,
        distance=models.Distance.COSINE,
    ),
)
print(f"Created collection: {COLLECTION_NAME}")

# Generate embeddings
print("Encoding documents into vector embeddings...")
texts = [doc["text"] for doc in documents]
vectors = embedding_model.encode(
    texts,
    batch_size=64,
    show_progress_bar=True,
    normalize_embeddings=True,
)

# Store in Qdrant in batches
print("Indexing points into Qdrant...")
points = []
for document, vector in zip(documents, vectors):
    point = models.PointStruct(
        id=str(uuid.uuid4()),
        vector=vector.tolist(),
        payload={
            "filename": document["filename"],
            "text": document["text"],
        },
    )
    points.append(point)

BATCH_SIZE = 500
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i : i + BATCH_SIZE]
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=batch,
    )
    print(f"  Upserted {i + len(batch)} / {len(points)} vectors...")

# Close client cleanly
client.close()

print()
print("========================================")
print(" Knowledge base ingestion complete!")
print("========================================")
print(f" Total documents indexed : {len(points)}")
print(f" Collection name          : {COLLECTION_NAME}")
print(f" Vector Database location : {QDRANT_PATH}")
print("========================================")

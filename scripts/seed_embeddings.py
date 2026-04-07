from __future__ import annotations
import sys
import os
sys.path.insert(0, ".")
os.environ.setdefault("DATABASE_URL", "postgresql://cybermind_db_user:rcTm7NNlUz1QT4QQXyMB0PR4Qb5xI0bu@dpg-d79t91ma2pns73ea0m7g-a.oregon-postgres.render.com/cybermind_db")

from src.backend.database.db_models import EmbeddingDB
from src.backend.database.engine import SessionLocal
from src.backend.services.mitre_loader import load_normalized
from src.backend.services.embedding_service import get_embedding_service
from langchain.text_splitter import RecursiveCharacterTextSplitter

print("Loading MITRE techniques...")
techniques = load_normalized()
print(f"Loaded {len(techniques)} techniques")

print("Loading embedding model...")
embedding_svc = get_embedding_service()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ". ", " "],
)

db = SessionLocal()
existing = db.query(EmbeddingDB).count()
if existing > 0:
    print(f"Embeddings already exist ({existing} rows). Skipping.")
    db.close()
    sys.exit(0)

print("Computing embeddings and storing in PostgreSQL...")
total = 0
for i, technique in enumerate(techniques):
    text = technique.get("text", "")
    chunks = splitter.split_text(text)
    for j, chunk in enumerate(chunks):
        vector = embedding_svc.embed_text(chunk).tolist()
        chunk_id = f"{technique['threat_id']}_{j}"
        db.add(EmbeddingDB(
            chunk_id=chunk_id,
            threat_id=technique["threat_id"],
            chunk_text=chunk,
            vector=vector,
            source="MITRE ATT&CK",
            metadata_=technique.get("metadata", {}),
        ))
        total += 1
    if (i + 1) % 50 == 0:
        db.commit()
        print(f"  Processed {i+1}/{len(techniques)} techniques, {total} chunks so far...")

db.commit()
db.close()
print(f"Done! Stored {total} embeddings in PostgreSQL.")

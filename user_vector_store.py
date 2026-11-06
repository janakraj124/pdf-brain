# user_vector_store.py — Per-User Vector DB
import os
import shutil
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from user_reader import read_user_pdfs
from chunker import chunk_all
from user_manager import get_user_db_path

print("📥 Embedding model load हुँदै...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding तयार")

print("📥 Reranker load हुँदै...")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("✅ Reranker तयार\n")


def get_user_collection(username):
    """User को collection लिने"""
    db_path = get_user_db_path(username)
    client = chromadb.PersistentClient(path=db_path)
    return client.get_or_create_collection("user_docs")


def build_user_database(username, reset=False):
    """User को database बनाउने"""
    db_path = get_user_db_path(username)
    
    if reset:
        parent = os.path.dirname(db_path)
        if os.path.exists(parent):
            try:
                shutil.rmtree(parent)
            except Exception:
                pass
        os.makedirs(parent, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection("user_docs")
    
    # पुरानो हटाउने
    try:
        if collection.count() > 0:
            collection.delete(where={})
    except Exception:
        pass
    
    # PDF पढ्ने
    print(f"📚 {username} को PDF पढ्दै...\n")
    texts = read_user_pdfs(username)
    
    if not texts:
        print(f"❌ {username} को कुनै PDF छैन")
        return None
    
    chunks = chunk_all(texts)
    print(f"✂️  {len(chunks)} chunks\n")
    
    # Embeddings
    print("🔄 Embedding बन्दै...")
    texts_list = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts_list, show_progress_bar=True, batch_size=32
    ).tolist()
    
    collection.add(
        documents=texts_list,
        embeddings=embeddings,
        ids=[c["id"] for c in chunks],
        metadatas=[{"source": c["source"]} for c in chunks]
    )
    
    print(f"✅ {len(chunks)} chunks {username} को DB मा")
    return collection


def user_search(username, query, n=4):
    """User को PDF मा खोज्ने"""
    collection = get_user_collection(username)
    
    if collection.count() == 0:
        return [], []
    
    q_emb = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=q_emb,
        n_results=min(n * 2, collection.count())
    )
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    
    if not docs:
        return [], []
    
    # Rerank
    pairs = [[query, doc] for doc in docs]
    scores = reranker.predict(pairs)
    
    ranked = sorted(
        zip(docs, metas, scores),
        key=lambda x: x[2],
        reverse=True
    )[:n]
    
    return [r[0] for r in ranked], [r[1] for r in ranked]


def user_database_stats(username):
    """User को DB stats"""
    try:
        collection = get_user_collection(username)
        return {"chunks": collection.count()}
    except Exception:
        return {"chunks": 0}
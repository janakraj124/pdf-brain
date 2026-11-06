# vector_store.py — Level 4 (Tag Filter सहित)
import os
import shutil
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from reader import read_all_docs
from chunker import chunk_all

# ============================================================
# Models
# ============================================================
print("📥 Embedding model load हुँदै...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model तयार")

print("📥 Reranker model load हुँदै...")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("✅ Reranker तयार\n")


# ============================================================
# BM25 Cache
# ============================================================
_bm25_cache = {
    "docs": None,
    "metas": None,
    "bm25": None
}


def _build_bm25_cache():
    """BM25 index बनाउने"""
    collection = get_collection()
    data = collection.get()
    all_docs = data.get("documents", [])
    all_metas = data.get("metadatas", [])
    
    if not all_docs:
        return None, None, None
    
    tokenized = [doc.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized)
    
    _bm25_cache["docs"] = all_docs
    _bm25_cache["metas"] = all_metas
    _bm25_cache["bm25"] = bm25
    
    return all_docs, all_metas, bm25


def _get_bm25():
    """BM25 cache लिने (वा बनाउने)"""
    if _bm25_cache["bm25"] is None:
        _build_bm25_cache()
    return (
        _bm25_cache["bm25"],
        _bm25_cache["docs"],
        _bm25_cache["metas"]
    )


def _invalidate_cache():
    """Cache invalidate गर्ने"""
    _bm25_cache["bm25"] = None
    _bm25_cache["docs"] = None
    _bm25_cache["metas"] = None


# ============================================================
# Database
# ============================================================
def build_database(reset=False):
    """Database बनाउने (वा rebuild गर्ने)"""
    db_path = "./chroma_db"
    
    if reset and os.path.exists(db_path):
        print("🗑️  पुरानो database हटाउँदै...")
        try:
            shutil.rmtree(db_path)
        except PermissionError:
            import time
            old_name = f"{db_path}_old_{int(time.time())}"
            try:
                os.rename(db_path, old_name)
                print(f"   ⚠️  '{old_name}' मा सारियो")
            except Exception as e:
                print(f"   ⚠️  Skip: {e}")
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection("docs")
    
    # पुरानो data हटाउने
    try:
        if collection.count() > 0:
            collection.delete(where={})
    except Exception:
        pass
    
    # PDF पढ्ने
    print("📚 PDF पढ्दै...\n")
    texts = read_all_docs()
    
    if not texts:
        print("❌ कुनै document छैन!")
        return None
    
    # Chunks बनाउने
    chunks = chunk_all(texts)
    print(f"✂️  {len(chunks)} chunks बने\n")
    
    # Embeddings
    print("🔄 Embedding बन्दै...")
    texts_list = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts_list,
        show_progress_bar=True,
        batch_size=32
    ).tolist()
    
    # Store
    collection.add(
        documents=texts_list,
        embeddings=embeddings,
        ids=[c["id"] for c in chunks],
        metadatas=[{"source": c["source"]} for c in chunks]
    )
    
    print(f"\n✅ {len(chunks)} chunks database मा")
    
    # Cache invalidate
    _invalidate_cache()
    
    return collection


def get_collection():
    """Existing database लिने"""
    client = chromadb.PersistentClient(path="./chroma_db")
    return client.get_or_create_collection("docs")


# ============================================================
# Tag Filter Helper
# ============================================================
def _get_allowed_pdfs(tag_filter=None):
    """
    Tag filter अनुसार allowed PDFs को set लिने।
    tag_filter None भए सबै PDFs allowed।
    """
    if not tag_filter:
        return None
    
    try:
        from tags import get_pdfs_by_tags
        allowed = set(get_pdfs_by_tags(tag_filter, match_all=False))
        return allowed if allowed else set()  # Empty set = कुनै match छैन
    except Exception:
        return None


# ============================================================
# Search Functions
# ============================================================
def semantic_search(query, n=10, allowed_pdfs=None):
    """Vector similarity search"""
    collection = get_collection()
    
    if collection.count() == 0:
        return []
    
    q_emb = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=q_emb,
        n_results=min(n, collection.count())
    )
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    
    hits = []
    for d, m in zip(docs, metas):
        source = m.get("source", "")
        
        # Tag filter
        if allowed_pdfs is not None and source not in allowed_pdfs:
            continue
        
        hits.append({
            "text": d,
            "source": source,
            "method": "semantic"
        })
    
    return hits


def keyword_search(query, n=10, allowed_pdfs=None):
    """BM25 keyword search"""
    bm25, all_docs, all_metas = _get_bm25()
    
    if not bm25 or not all_docs:
        return []
    
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    # Top n indices (filter सहित)
    indexed_scores = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    results = []
    for idx, score in indexed_scores:
        if score <= 0:
            continue
        if len(results) >= n:
            break
        
        source = all_metas[idx].get("source", "") if idx < len(all_metas) else ""
        
        # Tag filter
        if allowed_pdfs is not None and source not in allowed_pdfs:
            continue
        
        results.append({
            "text": all_docs[idx],
            "source": source,
            "method": "keyword"
        })
    
    return results


def rerank(query, candidates, top_n=4):
    """CrossEncoder ले candidates लाई rerank गर्ने"""
    if not candidates:
        return []
    
    # Deduplicate
    seen = set()
    unique = []
    for c in candidates:
        key = c["text"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(c)
    
    if not unique:
        return []
    
    # Rerank scores
    pairs = [[query, c["text"]] for c in unique]
    scores = reranker.predict(pairs)
    
    # Sort
    ranked = sorted(
        zip(unique, scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [c for c, s in ranked[:top_n]]


def hybrid_search(query, n=10, top_n=6, tag_filter=None):
    """
    पूरा search pipeline (Tag filter सहित):
    1. Tag filter → allowed PDFs
    2. Semantic + Keyword search
    3. Merge + deduplicate
    4. Rerank → top_n
    """
    # Step 1: Tag filter
    allowed_pdfs = _get_allowed_pdfs(tag_filter)
    
    # Empty set भए कुनै match छैन
    if allowed_pdfs is not None and len(allowed_pdfs) == 0:
        return []
    
    # Step 2: दुई search
    sem_results = semantic_search(query, n=n, allowed_pdfs=allowed_pdfs)
    kw_results = keyword_search(query, n=n, allowed_pdfs=allowed_pdfs)
    
    # Step 3: Merge
    all_candidates = sem_results + kw_results
    
    if not all_candidates:
        return []
    
    # Step 4: Rerank
    final = rerank(query, all_candidates, top_n=top_n)
    
    return final


# पुरानो function — backward compatible
def search(query, n=4, tag_filter=None):
    """Hybrid search wrapper (पुरानो format)"""
    results = hybrid_search(query, n=10, top_n=n, tag_filter=tag_filter)
    
    docs = [r["text"] for r in results]
    metas = [{"source": r["source"]} for r in results]
    
    return docs, metas


# ============================================================
# Tag Stats Helper
# ============================================================
def get_pdf_count():
    """Database मा कति unique PDF छन्"""
    collection = get_collection()
    if collection.count() == 0:
        return 0
    
    data = collection.get()
    sources = set()
    for m in data.get("metadatas", []):
        sources.add(m.get("source", ""))
    return len(sources)


def list_pdfs_in_db():
    """Database मा भएका PDFs को list"""
    collection = get_collection()
    if collection.count() == 0:
        return []
    
    data = collection.get()
    sources = set()
    for m in data.get("metadatas", []):
        s = m.get("source", "")
        if s:
            sources.add(s)
    return sorted(sources)


# ============================================================
# Test
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 vector_store.py Test (Tag Filter सहित)")
    print("=" * 60 + "\n")
    
    # 1. Database check
    count = get_pdf_count()
    print(f"📄 PDFs in DB: {count}")
    
    if count == 0:
        print("\n⚠️  Database खाली छ।")
        print("   Rebuild गर्न:")
        print("   >>> build_database(reset=True)")
        print("\n   वा Terminal मा:")
        print("   >>> python vector_store.py")
        exit()
    
    # 2. PDFs list
    print(f"\n📚 PDFs:")
    for pdf in list_pdfs_in_db():
        print(f"   • {pdf}")
    
    # 3. Tag filter test
    print("\n" + "=" * 60)
    print("🔍 Tag Filter Test")
    print("=" * 60 + "\n")
    
    try:
        from tags import get_all_tags, get_pdfs_by_tags
        
        all_tags = get_all_tags()
        
        if all_tags:
            print(f"🏷️  All tags: {all_tags}")
            
            for tag in all_tags[:3]:  # पहिलो 3 tags
                pdfs = get_pdfs_by_tags([tag])
                print(f"\n   Tag '{tag}' → {len(pdfs)} PDFs")
                for p in pdfs:
                    print(f"      • {p}")
        else:
            print("⚠️  कुनै tags छैन। tags.py चलाउनुहोस्:")
            print("   >>> python tags.py")
    except ImportError:
        print("⚠️  tags.py भेटिएन।")
    
    # 4. Search test
    print("\n" + "=" * 60)
    print("💬 Search Test")
    print("=" * 60 + "\n")
    
    test_query = "यो document कसको हो?"
    
    print(f"📝 Query: {test_query}\n")
    print("--- Tag filter बिना ---")
    results = hybrid_search(test_query, n=10, top_n=3)
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r['method']}] {r['source']}")
        print(f"     {r['text'][:100]}...")
    
    # With tag filter
    try:
        from tags import get_all_tags
        all_tags = get_all_tags()
        
        if all_tags:
            test_tag = all_tags[0]
            print(f"\n--- Tag filter: [{test_tag}] ---")
            results = hybrid_search(test_query, n=10, top_n=3, tag_filter=[test_tag])
            
            if not results:
                print("  ⚠️  यो tag मा कुनै match छैन")
            else:
                for i, r in enumerate(results, 1):
                    print(f"  {i}. [{r['method']}] {r['source']}")
                    print(f"     {r['text'][:100]}...")
    except Exception as e:
        print(f"Tag test skip: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete")
    print("=" * 60)
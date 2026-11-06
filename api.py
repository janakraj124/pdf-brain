# api.py — PDF Brain REST API
import os
import json
import secrets
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from answer import answer_question
from tags import get_all_tags, get_pdfs_by_tags

# ============================================================
# FastAPI Setup
# ============================================================
app = FastAPI(
    title="PDF Brain API",
    description="AI-powered PDF Q&A REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — कुनै पनि client बाट access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API Keys Storage
# ============================================================
API_KEYS_FILE = "api_keys.json"


def load_api_keys():
    if not os.path.exists(API_KEYS_FILE):
        return {}
    try:
        with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_api_keys(keys):
    with open(API_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)


def create_api_key(name, username="admin", rate_limit=100):
    """नयाँ API key बनाउने"""
    keys = load_api_keys()
    key = "pb_" + secrets.token_urlsafe(32)
    
    keys[key] = {
        "name": name,
        "username": username,
        "created": datetime.now().isoformat(),
        "active": True,
        "requests_today": 0,
        "requests_total": 0,
        "rate_limit": rate_limit,
        "last_reset": datetime.now().strftime("%Y-%m-%d")
    }
    save_api_keys(keys)
    return key


def verify_api_key(api_key):
    """API key validate + rate limit check"""
    keys = load_api_keys()
    
    if api_key not in keys:
        return None
    
    key_data = keys[api_key]
    
    if not key_data.get("active", True):
        return None
    
    # Reset daily counter
    today = datetime.now().strftime("%Y-%m-%d")
    if key_data.get("last_reset") != today:
        key_data["requests_today"] = 0
        key_data["last_reset"] = today
        keys[api_key] = key_data
        save_api_keys(keys)
    
    # Rate limit check
    if key_data.get("requests_today", 0) >= key_data.get("rate_limit", 100):
        return None
    
    # Increment counters
    key_data["requests_today"] = key_data.get("requests_today", 0) + 1
    key_data["requests_total"] = key_data.get("requests_total", 0) + 1
    keys[api_key] = key_data
    save_api_keys(keys)
    
    return key_data


def get_api_key_from_header(x_api_key: Optional[str] = Header(None)):
    """API key header बाट लिने"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key चाहिन्छ। X-API-Key header मा राख्नुहोस्।"
        )
    
    key_data = verify_api_key(x_api_key)
    
    if not key_data:
        raise HTTPException(
            status_code=401,
            detail="गलत वा expired API key"
        )
    
    return key_data


# ============================================================
# Request / Response Models
# ============================================================
class AskRequest(BaseModel):
    question: str
    tag_filter: Optional[List[str]] = None
    username: Optional[str] = "api_user"


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    response_time: float


class CreateKeyRequest(BaseModel):
    name: str
    username: str = "admin"
    rate_limit: int = 100


class HealthResponse(BaseModel):
    status: str
    version: str
    pdfs: int
    chunks: int
    timestamp: str


# ============================================================
# Public Endpoints
# ============================================================
@app.get("/")
def root():
    """API root"""
    return {
        "name": "PDF Brain API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check"""
    import chromadb
    
    pdfs = 0
    if os.path.exists("docs"):
        pdfs = len([f for f in os.listdir("docs") if f.lower().endswith(".pdf")])
    
    chunks = 0
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("docs")
        chunks = collection.count()
    except Exception:
        pass
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        pdfs=pdfs,
        chunks=chunks,
        timestamp=datetime.now().isoformat()
    )


# ============================================================
# Protected Endpoints (API Key Required)
# ============================================================
@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    key_data: dict = Depends(get_api_key_from_header)
):
    """
    PDF बारे प्रश्न सोध्ने
    
    Headers:
    - X-API-Key: तपाईंको API key
    
    Body:
    {
        "question": "यो document कसको हो?",
        "tag_filter": ["financial"],
        "username": "api_user"
    }
    """
    import time
    
    if not request.question or len(request.question.strip()) < 2:
        raise HTTPException(400, "प्रश्न खाली छ")
    
    start = time.time()
    
    try:
        result = answer_question(
            request.question,
            username=f"api_{key_data.get('username', 'user')}",
            tag_filter=request.tag_filter
        )
        
        elapsed = time.time() - start
        
        return AskResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            response_time=round(elapsed, 2)
        )
    except Exception as e:
        raise HTTPException(500, f"AI error: {str(e)}")


@app.get("/tags")
def get_tags_endpoint(key_data: dict = Depends(get_api_key_from_header)):
    """
    सबै tags लिने
    
    Headers:
    - X-API-Key: तपाईंको API key
    """
    try:
        tags = get_all_tags()
        result = []
        for tag in tags:
            pdfs = get_pdfs_by_tags([tag])
            result.append({
                "tag": tag,
                "pdf_count": len(pdfs),
                "pdfs": pdfs
            })
        return {"tags": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(500, f"Tags error: {str(e)}")


@app.get("/pdfs")
def list_pdfs(key_data: dict = Depends(get_api_key_from_header)):
    """
    सबै PDF list
    
    Headers:
    - X-API-Key: तपाईंको API key
    """
    pdfs = []
    if os.path.exists("docs"):
        for f in os.listdir("docs"):
            if f.lower().endswith(".pdf"):
                try:
                    from tags import get_pdf_tags
                    tags = get_pdf_tags(f)
                except Exception:
                    tags = []
                
                pdfs.append({
                    "name": f,
                    "tags": tags,
                    "size": os.path.getsize(os.path.join("docs", f))
                })
    
    return {"pdfs": pdfs, "total": len(pdfs)}


@app.get("/me")
def me(key_data: dict = Depends(get_api_key_from_header)):
    """
    API key को info
    
    Headers:
    - X-API-Key: तपाईंको API key
    """
    return {
        "name": key_data.get("name"),
        "username": key_data.get("username"),
        "created": key_data.get("created"),
        "requests_today": key_data.get("requests_today", 0),
        "requests_total": key_data.get("requests_total", 0),
        "rate_limit": key_data.get("rate_limit", 100),
        "remaining": key_data.get("rate_limit", 100) - key_data.get("requests_today", 0)
    }


# ============================================================
# Admin Endpoints
# ============================================================
@app.post("/admin/keys")
def create_key(
    request: CreateKeyRequest,
    admin_password: str = Header(...)
):
    """
    नयाँ API key बनाउने (Admin मात्र)
    
    Headers:
    - admin-password: तपाईंको admin password
    """
    from auth import verify_user
    ok, user = verify_user("admin", admin_password)
    
    if not ok or user.get("role") != "admin":
        raise HTTPException(403, "Admin access चाहिन्छ")
    
    key = create_api_key(
        name=request.name,
        username=request.username,
        rate_limit=request.rate_limit
    )
    
    return {
        "api_key": key,
        "name": request.name,
        "rate_limit": request.rate_limit,
        "message": "यो key एकैचोटि मात्र देखिन्छ — save गर्नुहोस्!"
    }


@app.get("/admin/keys")
def list_keys(admin_password: str = Header(...)):
    """सबै API keys list (Admin मात्र)"""
    from auth import verify_user
    ok, user = verify_user("admin", admin_password)
    
    if not ok or user.get("role") != "admin":
        raise HTTPException(403, "Admin access चाहिन्छ")
    
    keys = load_api_keys()
    
    result = []
    for key, data in keys.items():
        result.append({
            "key_preview": key[:15] + "...",
            "name": data.get("name"),
            "username": data.get("username"),
            "created": data.get("created"),
            "active": data.get("active", True),
            "requests_total": data.get("requests_total", 0),
            "requests_today": data.get("requests_today", 0),
            "rate_limit": data.get("rate_limit", 100)
        })
    
    return {"keys": result, "total": len(result)}


@app.delete("/admin/keys/{key_preview}")
def revoke_key(key_preview: str, admin_password: str = Header(...)):
    """API key revoke (Admin मात्र)"""
    from auth import verify_user
    ok, user = verify_user("admin", admin_password)
    
    if not ok or user.get("role") != "admin":
        raise HTTPException(403, "Admin access चाहिन्छ")
    
    keys = load_api_keys()
    
    for key in keys:
        if key.startswith(key_preview.replace("...", "")):
            keys[key]["active"] = False
            save_api_keys(keys)
            return {"message": "Key revoke भयो", "key_preview": key[:15] + "..."}
    
    raise HTTPException(404, "Key भेटिएन")


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🌐 PDF Brain — REST API")
    print("=" * 60)
    print("📖 Docs:   http://localhost:8000/docs")
    print("❤️  Health: http://localhost:8000/health")
    print("🛑 बन्द:   Ctrl + C")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
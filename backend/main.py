import hashlib
import json
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

from services.agent_service import route_question
from services.agentic_agent_service import route_question_agentic
from services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from services.validation_service import validation_service
from services.secrets_service import secrets_manager
from services.csrf_service import csrf_protection
from services.database_service import (
    create_user,
    delete_conversation,
    get_history,
    get_messages,
    get_user_by_username,
    init_database,
    save_turn,
)
from services.document_service import (
    build_index_from_uploaded_pdfs,
    delete_uploaded_pdf,
    get_user_upload_dir,
    list_uploaded_pdfs,
)
from services.llm import test_api_key

load_dotenv()

logger = logging.getLogger("enterprise_agent")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

# Validate secrets on startup
secret_validation = secrets_manager.validate_secrets()
if not secret_validation["valid"]:
    logger.warning(f"Secret validation failed: {secret_validation}")
if secret_validation["warnings"]:
    logger.warning(f"Secret validation warnings: {secret_validation['warnings']}")

init_database()
request_buckets = defaultdict(deque)
RATE_LIMITS = {"/api/auth/login": (5, 60), "/api/chat": (30, 60)}

app = FastAPI(
    title="Cogniflow",
    description="RAG assistant with tools, PDF upload, and SQLite memory",
    version="1.3.0",
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str | None = Field(default=None, max_length=100)
    agentic: bool = Field(default=False, description="Use agentic RAG system")


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)


allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# HTTPS Redirect Middleware (uncomment for production)
# app.add_middleware(HTTPSRedirectMiddleware)

# Trusted Host Middleware (uncomment for production with specific domains)
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])


@app.middleware("http")
async def request_context(request, call_next):
    request_id = str(uuid4())
    client = request.client.host if request.client else "unknown"
    limit = RATE_LIMITS.get(request.url.path)
    if limit:
        max_requests, window = limit
        bucket = request_buckets[(client, request.url.path)]
        now = time.monotonic()
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if len(bucket) >= max_requests:
            response = JSONResponse(
                {"detail": "Too many requests. Try again later."},
                status_code=429,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        bucket.append(now)

    started = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        logger.info(json.dumps({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }))
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/")
def root():
    return {
        "message": "CogniFlow Enterprise AI Assistant is running",
        "version": "2.0.0",
        "security": "Enhanced with input validation, security headers, and PostgreSQL support"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/test-groq")
def test_groq_api():
    """Test endpoint to verify Groq API key and model access."""
    result = test_api_key()
    
    if result["status"] == "valid":
        return {
            "status": "✅ SUCCESS",
            "message": "Your Groq API key is valid and working!",
            "model_used": result["model_used"],
            "next_step": "You can now use the chatbot normally.",
        }
    else:
        return {
            "status": "❌ FAILED",
            "message": "Your Groq API key is not working properly.",
            "error": result["error"],
            "steps_to_fix": [
                "1. Go to https://console.groq.com/keys",
                "2. Delete your current API key",
                "3. Create a NEW API key",
                "4. Copy the new key and update your .env file",
                "5. Restart the backend",
                "6. Try this test again",
            ],
        }


@app.get("/api/debug/retrieval")
def debug_retrieval(
    question: str,
    current_user: dict = Depends(get_current_user),
):
    """Debug endpoint to see what's being retrieved for a question."""
    try:
        from services.rag_service import retrieve_documents
        from services.document_service import list_uploaded_pdfs
        
        # Get list of uploaded PDFs
        pdfs = list_uploaded_pdfs(current_user["id"])
        
        # Retrieve documents for the question
        docs = retrieve_documents(question, current_user["id"])
        
        return {
            "question": question,
            "uploaded_pdfs": pdfs,
            "retrieved_documents": [
                {
                    "filename": doc["filename"],
                    "similarity": doc["similarity"],
                    "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "content_length": len(doc["content"]),
                }
                for doc in docs[:10]
            ]
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}


@app.get("/api/debug/extracted-text")
def debug_extracted_text(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    """Debug endpoint to see what text was extracted from a PDF."""
    try:
        from services.document_service import extract_text_from_pdf, get_user_upload_dir
        from pathlib import Path
        
        upload_dir = get_user_upload_dir(current_user["id"])
        pdf_path = upload_dir / filename
        
        if not pdf_path.exists():
            return {"error": f"File {filename} not found"}
        
        text = extract_text_from_pdf(pdf_path)
        
        return {
            "filename": filename,
            "total_characters": len(text),
            "first_500_chars": text[:500],
            "last_500_chars": text[-500:] if len(text) > 500 else text,
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}


@app.get("/ready")
def readiness():
    try:
        init_database()
        return {"status": "ready"}
    except Exception as error:
        raise HTTPException(status_code=503, detail="Service is not ready.") from error


@app.get("/api/security/csrf-token")
def get_csrf_token():
    """Get a CSRF token for protected operations."""
    return csrf_protection.get_csrf_token_endpoint()


@app.post("/api/documents/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    upload_dir = get_user_upload_dir(current_user["id"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    seen_uploads = set()

    for file in files:
        filename = Path(file.filename or "").name

        # Validate filename
        filename_validation = validation_service.validate_filename(filename)
        if not filename_validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filename: {filename_validation.errors[0]}",
            )

        sanitized_filename = filename_validation.sanitized_value

        if (
            not sanitized_filename
            or not sanitized_filename.lower().endswith(".pdf")
        ):
            raise HTTPException(
                status_code=400,
                detail=f"{sanitized_filename} is not a PDF file.",
            )

        destination = upload_dir / sanitized_filename
        contents = await file.read(MAX_UPLOAD_BYTES + 1)

        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="PDF exceeds the 10 MB limit.")

        if not contents.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail=f"{sanitized_filename} is not a readable PDF.")

        fingerprint = (sanitized_filename, hashlib.sha256(contents).hexdigest())
        if fingerprint in seen_uploads:
            continue
        seen_uploads.add(fingerprint)
        destination.write_bytes(contents)

        saved_files.append(sanitized_filename)

    try:
        result = build_index_from_uploaded_pdfs(current_user["id"])
    except (ValueError, FileNotFoundError) as error:
        logger.error(f"Index build failed: {error}")
        for filename in saved_files:
            (upload_dir / filename).unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected error during index build")
        for filename in saved_files:
            (upload_dir / filename).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to index PDF: {str(error)}") from error

    return {
        "message": "Your PDF files were uploaded and indexed.",
        "uploaded_files": saved_files,
        **result,
    }
@app.post("/api/documents/rebuild-index")
def rebuild_index(
    current_user: dict = Depends(get_current_user),
):
    try:
        return build_index_from_uploaded_pdfs(current_user["id"])
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    # Validate question
    question_validation = validation_service.validate_question(request.question)
    if not question_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": question_validation.errors}
        )
    
    # Validate session ID
    session_validation = validation_service.validate_session_id(request.session_id)
    if not session_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": session_validation.errors}
        )
    
    session_id = session_validation.sanitized_value or str(uuid4())

    try:
        history = get_history(
            current_user["id"],
            session_id,
        )

        # Choose between agentic and original routing
        if request.agentic:
            result = route_question_agentic(
                question_validation.sanitized_value,
                history,
                current_user["id"],
                session_id,
            )
        else:
            result = route_question(
                question_validation.sanitized_value,
                history,
                current_user["id"],
                request.agentic,
            )
        
        save_turn(
            current_user["id"],
            session_id,
            question_validation.sanitized_value,
            result["answer"],
        )

        return {
            "session_id": session_id,
            **result,
        }

    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.exception("Chat processing failed")
        raise HTTPException(
            status_code=503,
            detail="The assistant service is temporarily unavailable. Please try again shortly.",
        ) from error


@app.get("/api/conversations/{session_id}")

def conversation_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    return {
        "session_id": session_id,
        "messages": get_messages(current_user["id"], session_id),
    }


@app.delete("/api/conversations/{session_id}")
def clear_conversation(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        delete_conversation(current_user["id"], session_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    return {
        "message": "Conversation deleted.",
        "session_id": session_id,
    }

@app.post("/api/auth/register")
def register(request: RegisterRequest):
    # Validate username
    username_validation = validation_service.validate_username(request.username)
    if not username_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": username_validation.errors, "warnings": username_validation.warnings}
        )
    
    # Validate password
    password_validation = validation_service.validate_password(request.password)
    if not password_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": password_validation.errors, "warnings": password_validation.warnings}
        )
    
    try:
        user = create_user(
            username_validation.sanitized_value,
            hash_password(request.password),
        )

        return {
            "message": "User registered successfully.",
            "user": user,
        }

    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/auth/login")
def login(request: LoginRequest):
    # Validate username
    username_validation = validation_service.validate_username(request.username)
    if not username_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": username_validation.errors}
        )
    
    # Validate password
    password_validation = validation_service.validate_password(request.password)
    if not password_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": password_validation.errors}
        )
    
    user = get_user_by_username(username_validation.sanitized_value)

    if not user or not verify_password(
        request.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        user["id"],
        user["username"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }

@app.get("/api/documents")
def list_documents(
    current_user: dict = Depends(get_current_user),
):
    return {
        "documents": list_uploaded_pdfs(
            current_user["id"]
        )
    }


@app.delete("/api/documents/{filename}")
def delete_document(
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        return delete_uploaded_pdf(
            current_user["id"],
            filename,
        )

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

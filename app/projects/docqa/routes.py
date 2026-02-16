"""Doc QA API Routes - Document Question & Answering System with i18n + HTMX Support"""
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
import logging
import tempfile

from .models import (
    QueryRequest, QueryResponse, UploadResponse,
    HealthCheck, DocumentStatus,
)
from .services.document_processor import DocumentProcessor
from .services.embeddings import get_embedding_service
from .services.vector_store import get_vector_store
from .services.retrieval import get_retrieval_service
from .services.generation import get_generation_service
from .services.verification import get_verification_service
from .services.rate_limiter import get_rate_limiter
from .config import rag_config
from .i18n import t, get_language_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/docqa", tags=["Doc QA"])

templates = Jinja2Templates(
    directory=[
        str(Path(__file__).parent / "templates"),
        str(Path(__file__).resolve().parent.parent.parent.parent / "templates"),
    ]
)

templates.env.globals["t"] = t


@router.get("/", response_class=HTMLResponse)
async def docqa_index(request: Request):
    """Main Doc QA interface with i18n"""
    lang = get_language_from_request(request)
    return templates.TemplateResponse(
        "docqa_index.html",
        {"request": request, "lang": lang}
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload and index document - HTMX endpoint"""
    start = time.time()
    lang = get_language_from_request(request)
    
    try:
        ext = Path(file.filename).suffix.lower()
        if ext not in rag_config.ALLOWED_EXTENSIONS:
            return f'<div class="result error">{t("upload_error_type", lang, ext=ext)}</div>'
        
        content = await file.read()
        max_bytes = rag_config.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            return f'<div class="result error">{t("upload_error_size", lang, max_mb=rag_config.MAX_FILE_SIZE_MB)}</div>'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            processor = DocumentProcessor()
            chunks, metadatas = processor.process_file(tmp_path, file.filename)

            vs = get_vector_store()
            doc_id = metadatas[0].document_id
            if vs.document_exists(doc_id):
                vs.delete_document(doc_id)
                logger.info(f"Replaced existing document: {doc_id}")

            emb_service = get_embedding_service()
            embeddings = emb_service.embed_documents(chunks)
            vs.add_documents(chunks, embeddings, metadatas)
            
            elapsed = (time.time() - start) * 1000
            
            return f'''<div class="result success">
                {t("upload_success", lang, filename=file.filename, chunks=len(chunks), time_ms=elapsed)}
            </div>'''
        
        finally:
            tmp_path.unlink(missing_ok=True)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return f'<div class="result error">{t("upload_error", lang, error=str(e))}</div>'


@router.post("/query", response_class=HTMLResponse)
async def query_documents(
    request: Request,
    question: str = Form(...),
    enable_verification: str = Form("false"),
    top_k: int = Form(5)
):
    """Query documents - HTMX endpoint"""
    start = time.time()
    lang = get_language_from_request(request)
    enable_verify = enable_verification.lower() == "true"

    client_ip = request.client.host if request.client else "unknown"
    limiter = get_rate_limiter()
    allowed, remaining = limiter.check(client_ip)
    if not allowed:
        return f'<div class="result error">{t("query_rate_limited", lang, limit=rag_config.RATE_LIMIT_MONTHLY)}</div>'

    try:
        retrieval = get_retrieval_service()
        chunks = await retrieval.retrieve(question, top_k=top_k)
        
        if not chunks:
            return f'<div class="result">{t("query_no_documents", lang)}</div>'
        
        gen = get_generation_service()
        result = await gen.generate(question, chunks)
        remaining = limiter.increment(client_ip)

        verification_html = ""
        confidence = 0.8
        
        if enable_verify:
            verifier = get_verification_service()
            steps = verifier.verify(result["answer"], chunks)
            confidence = sum(s.confidence for s in steps) / max(len(steps), 1)
            
            steps_html = "".join([
                f'''<div class="verification-step">
                    {t("verification_step", lang,
                       step=s.step,
                       status=t("verification_passed" if s.passed else "verification_failed", lang),
                       confidence=s.confidence)}
                    <br><small>{s.details}</small>
                </div>'''
                for s in steps
            ])
            
            verification_html = f'''<div class="verification">
                <h4>{t("verification_title", lang)}</h4>
                {steps_html}
            </div>'''
        
        sources_html = "".join([
            f'''<div class="source">
                [{i+1}] <strong>{c.metadata.filename}</strong>
                (p. {c.metadata.page_number}, chunk {c.metadata.chunk_index}/{c.metadata.total_chunks})
                <br><small>Score: {c.score:.3f}</small>
            </div>'''
            for i, c in enumerate(chunks[:3])
        ])
        
        elapsed = (time.time() - start) * 1000
        
        return f'''<div class="result answer">
            <h3>{t("query_answer_title", lang)}</h3>
            <p>{result["answer"]}</p>
            
            <h3>{t("query_sources_title", lang)}</h3>
            <div class="sources">{sources_html}</div>
            
            {verification_html}
            
            <div class="metadata">
                {t("query_metadata", lang,
                   confidence=confidence,
                   time_ms=elapsed,
                   model=result.get("model", "unknown"))}
                <br><small>{t("query_remaining", lang,
                   remaining=remaining,
                   limit=rag_config.RATE_LIMIT_MONTHLY)}</small>
            </div>
        </div>'''
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        return f'<div class="result error">{t("query_error", lang, error=str(e))}</div>'


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """System health check"""
    emb_loaded = False
    vs_connected = False
    total_chunks = 0

    try:
        emb = get_embedding_service()
        _ = emb.model
        emb_loaded = True
    except Exception:
        pass

    try:
        vs = get_vector_store()
        stats = vs.get_stats()
        vs_connected = True
        total_chunks = stats.get("total_points", 0)
    except Exception:
        pass

    return HealthCheck(
        status="healthy" if emb_loaded and vs_connected else "degraded",
        embedding_model_loaded=emb_loaded,
        vector_store_connected=vs_connected,
        llm_provider=rag_config.LLM_PROVIDER,
        llm_available=bool(rag_config.GROQ_API_KEY or rag_config.PERPLEXITY_API_KEY),
        total_documents=0,
        total_chunks=total_chunks,
    )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    vs = get_vector_store()
    vs.delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}

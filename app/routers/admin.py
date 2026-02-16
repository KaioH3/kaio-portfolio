"""
Admin Dashboard Router
Monitoring and quota management for external APIs
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.middleware.rate_limit import get_global_rate_limiter
from app.middleware.quota_tracker import get_quota_tracker

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/quotas", response_class=JSONResponse)
async def get_quotas():
    """
    Dashboard de uso de quotas das APIs externas.

    Para recrutadores verem:
    - Demonstra monitoramento de custos
    - Arquitetura defensiva
    - Production readiness
    """

    # Rate limiter stats (hourly)
    rate_limiter = get_global_rate_limiter()
    rate_stats = rate_limiter.get_stats()

    # Quota tracker stats (cumulative)
    quota_tracker = get_quota_tracker()
    quota_usage = quota_tracker.get_usage_summary()

    # Qdrant real-time stats (lazy import to avoid dependency issues)
    try:
        from app.projects.docqa.services.vector_store import get_vector_store
        vs = get_vector_store()
        collection_info = vs.client.get_collection(vs.collection_name)
        qdrant_realtime = {
            "points_count": collection_info.points_count,
            "vectors_count": collection_info.vectors_count,
            "status": str(collection_info.status),
        }
    except Exception as e:
        qdrant_realtime = {"error": str(e)}

    return {
        "rate_limits_hourly": rate_stats,
        "quota_usage_cumulative": quota_usage,
        "qdrant_realtime": qdrant_realtime,
        "endpoints": {
            "voyage_embeddings": "/docqa/upload (document indexing)",
            "qdrant_writes": "/docqa/upload (vector storage)",
            "groq_queries": "/docqa/query (LLM generation)",
        },
    }

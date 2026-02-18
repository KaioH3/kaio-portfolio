"""
Generation Service - Multi-provider LLM
Priority: Groq (FREE) -> Perplexity -> OpenAI
"""
from typing import List, Dict, Any, Optional
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from fastapi import HTTPException

from ..config import rag_config
from ..models import RetrievedChunk
from app.middleware.rate_limit import get_global_rate_limiter
from app.middleware.quota_tracker import get_quota_tracker

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self):
        self.provider = rag_config.LLM_PROVIDER
        self.timeout = rag_config.REQUEST_TIMEOUT

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
    async def generate(
        self, query: str, context_chunks: List[RetrievedChunk],
        max_tokens: Optional[int] = None,
        lang: str = "en-US",
    ) -> Dict[str, Any]:
        # Rate limit check BEFORE calling LLM
        limiter = get_global_rate_limiter()
        if not limiter.check_and_increment("groq_queries"):
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit exceeded. Try again in 1 hour."
            )

        prompt = self._build_prompt(query, context_chunks, lang)
        providers = self._get_provider_chain()

        last_error = None
        for provider_name, provider_fn in providers:
            try:
                logger.info(f"Trying provider: {provider_name}")
                return await provider_fn(prompt, max_tokens)
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                last_error = e
                continue

        raise ValueError(f"All providers failed. Last error: {last_error}")

    def _get_provider_chain(self):
        """Return ordered list of (name, fn) to try"""
        chain = []
        if rag_config.GROQ_API_KEY:
            chain.append(("groq", self._generate_groq))
        if rag_config.PERPLEXITY_API_KEY:
            chain.append(("perplexity", self._generate_perplexity))
        if rag_config.OPENAI_API_KEY:
            chain.append(("openai", self._generate_openai))
        return chain

    def _build_prompt(self, query: str, chunks: List[RetrievedChunk], lang: str = "en-US") -> str:
        ctx_parts = []
        for i, c in enumerate(chunks[:3], 1):
            src = f"{c.metadata.filename} (chunk {c.metadata.chunk_index})"
            clean_text = " ".join(c.text.split())[:400]
            ctx_parts.append(f"[{i}] {src}\n{clean_text}")
        ctx = "\n\n".join(ctx_parts)

        if lang == "en-US":
            lang_rule = "Write your answer in English."
            no_info = "I don't have enough information in the document."
        else:
            lang_rule = "Escreva sua resposta em português."
            no_info = "Não encontrei informação suficiente no documento."

        return (
            "You are a document assistant. Read the SOURCES below and answer the QUESTION.\n\n"
            "RULES:\n"
            f"1. {lang_rule}\n"
            "2. Use 2-4 sentences only.\n"
            "3. Cite sources as [1], [2], [3].\n"
            "4. Do NOT copy code, commands, curly braces, or template text verbatim.\n"
            "5. Summarize in your own words.\n"
            f"6. If the answer is not in the sources, respond: \"{no_info}\"\n\n"
            "SOURCES:\n"
            f"{ctx}\n\n"
            f"QUESTION: {query}\n\n"
            "ANSWER:"
        )

    async def _generate_groq(self, prompt: str, max_tokens: Optional[int]) -> Dict[str, Any]:
        """Groq FREE tier - llama-3.1-8b-instant"""
        if not rag_config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {rag_config.GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": rag_config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or rag_config.GROQ_MAX_TOKENS,
            "temperature": 0.1,
            "frequency_penalty": 0.6,
            "presence_penalty": 0.3,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            r = resp.json()

            # Track tokens (Groq retorna usage no response)
            if "usage" in r:
                tracker = get_quota_tracker()
                tracker.record_groq_tokens(r["usage"]["total_tokens"])

            return {
                "answer": r["choices"][0]["message"]["content"],
                "tokens_used": {
                    "prompt": r["usage"]["prompt_tokens"],
                    "completion": r["usage"]["completion_tokens"],
                    "total": r["usage"]["total_tokens"],
                },
                "model": rag_config.GROQ_MODEL,
                "provider": "groq",
                "cost": 0.0,
            }

    async def _generate_perplexity(self, prompt: str, max_tokens: Optional[int]) -> Dict[str, Any]:
        if not rag_config.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not set")
        url = "https://api.perplexity.ai/chat/completions"
        headers = {"Authorization": f"Bearer {rag_config.PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": rag_config.PERPLEXITY_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or rag_config.PERPLEXITY_MAX_TOKENS,
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            r = resp.json()
            return {
                "answer": r["choices"][0]["message"]["content"],
                "tokens_used": {
                    "prompt": r["usage"]["prompt_tokens"],
                    "completion": r["usage"]["completion_tokens"],
                    "total": r["usage"]["total_tokens"],
                },
                "model": rag_config.PERPLEXITY_MODEL,
                "provider": "perplexity",
            }

    async def _generate_openai(self, prompt: str, max_tokens: Optional[int]) -> Dict[str, Any]:
        if not rag_config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=rag_config.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model=rag_config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or rag_config.OPENAI_MAX_TOKENS,
            temperature=0.2,
        )
        return {
            "answer": resp.choices[0].message.content,
            "tokens_used": {
                "prompt": resp.usage.prompt_tokens,
                "completion": resp.usage.completion_tokens,
                "total": resp.usage.total_tokens,
            },
            "model": rag_config.OPENAI_MODEL,
            "provider": "openai",
        }



_generation_service = None

def get_generation_service() -> GenerationService:
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service

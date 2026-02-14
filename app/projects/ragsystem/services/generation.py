"""
Generation Service
Multi-provider LLM support: Perplexity (primary), OpenAI, Ollama (free fallback)
"""
from typing import List, Dict, Any, Optional
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

from ..config import rag_config
from ..models import RetrievedChunk

logger = logging.getLogger(__name__)


class GenerationService:
    """LLM generation with multiple provider support"""
    
    def __init__(self):
        self.provider = rag_config.LLM_PROVIDER
        self.timeout = rag_config.REQUEST_TIMEOUT
        
        # Initialize clients
        self._openai_client = None
        self._perplexity_client = None
        self._ollama_client = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        query: str,
        context_chunks: List[RetrievedChunk],
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate answer from query and context
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            max_tokens: Max tokens in response
            
        Returns:
            Dict with answer, tokens_used, etc.
        """
        # Build prompt with context
        prompt = self._build_prompt(query, context_chunks)
        
        # Route to appropriate provider
        if self.provider == "perplexity":
            return await self._generate_perplexity(prompt, max_tokens)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, max_tokens)
        elif self.provider == "ollama":
            return await self._generate_ollama(prompt, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _build_prompt(
        self,
        query: str,
        context_chunks: List[RetrievedChunk]
    ) -> str:
        """Build RAG prompt with context"""
        # Format context
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source = f"{chunk.metadata.filename} (chunk {chunk.metadata.chunk_index})"
            context_parts.append(f"[{i}] {source}\n{chunk.text}\n")
        
        context_text = "\n".join(context_parts)
        
        # System prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on provided context.

IMPORTANT RULES:
1. ONLY use information from the provided context
2. If the context doesn't contain the answer, say "I don't have enough information to answer this question"
3. Always cite sources using [1], [2], etc. notation
4. Be concise and accurate
5. Never make up information"""
        
        # User prompt
        user_prompt = f"""Context:
{context_text}

Question: {query}

Answer based on the context above:"""
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    async def _generate_perplexity(
        self,
        prompt: str,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Generate using Perplexity API"""
        if not rag_config.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not set")
        
        if max_tokens is None:
            max_tokens = rag_config.PERPLEXITY_MAX_TOKENS
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {rag_config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": rag_config.PERPLEXITY_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,  # Low temp for factual answers
            "top_p": 0.9
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
        
        return {
            "answer": result["choices"][0]["message"]["content"],
            "tokens_used": {
                "prompt": result["usage"]["prompt_tokens"],
                "completion": result["usage"]["completion_tokens"],
                "total": result["usage"]["total_tokens"]
            },
            "model": rag_config.PERPLEXITY_MODEL
        }
    
    async def _generate_openai(
        self,
        prompt: str,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Generate using OpenAI API"""
        if not rag_config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")
        
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=rag_config.OPENAI_API_KEY)
        
        if max_tokens is None:
            max_tokens = rag_config.OPENAI_MAX_TOKENS
        
        response = self._openai_client.chat.completions.create(
            model=rag_config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2
        )
        
        return {
            "answer": response.choices[0].message.content,
            "tokens_used": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            },
            "model": rag_config.OPENAI_MODEL
        }
    
    async def _generate_ollama(
        self,
        prompt: str,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Generate using local Ollama (FREE fallback)"""
        url = f"{rag_config.OLLAMA_BASE_URL}/api/generate"
        
        payload = {
            "model": rag_config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": max_tokens or 1000
            }
        }
        
        async with httpx.AsyncClient(timeout=rag_config.OLLAMA_TIMEOUT) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                return {
                    "answer": result["response"],
                    "tokens_used": {
                        "prompt": result.get("prompt_eval_count", 0),
                        "completion": result.get("eval_count", 0),
                        "total": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                    },
                    "model": rag_config.OLLAMA_MODEL
                }
            except httpx.ConnectError:
                logger.error("Ollama not running. Install: curl https://ollama.ai/install.sh | sh")
                raise ValueError("Ollama not available. Please start Ollama or use another provider.")


# Global singleton
_generation_service = None

def get_generation_service() -> GenerationService:
    """Get or create global generation service instance"""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service

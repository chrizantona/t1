"""
SciBox LLM API Client
Wrapper for interacting with SciBox models using OpenAI-compatible API.
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
import asyncio
from functools import wraps
import time

from ..core.config import settings


class SciBoxClient:
    """Client for SciBox LLM API with rate limiting support."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.SCIBOX_API_KEY,
            base_url=settings.SCIBOX_BASE_URL
        )
        self.chat_model = settings.CHAT_MODEL
        self.coder_model = settings.CODER_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        
        # Rate limiting
        self._last_chat_request = 0
        self._last_coder_request = 0
        self._last_embedding_request = 0
        self._chat_interval = 1.0 / settings.CHAT_MODEL_RPS
        self._coder_interval = 1.0 / settings.CODER_MODEL_RPS
        self._embedding_interval = 1.0 / settings.EMBEDDING_MODEL_RPS
    
    def _rate_limit(self, last_request_time: float, interval: float) -> None:
        """Simple rate limiting - wait if needed."""
        elapsed = time.time() - last_request_time
        if elapsed < interval:
            time.sleep(interval - elapsed)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        model: Optional[str] = None
    ) -> str:
        """
        Send chat completion request to universal chat model (qwen3-32b-awq).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            model: Override default chat model
        
        Returns:
            Response content as string
        """
        self._rate_limit(self._last_chat_request, self._chat_interval)
        self._last_chat_request = time.time()
        
        response = self.client.chat.completions.create(
            model=model or self.chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def code_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> str:
        """
        Send completion request to code model (qwen3-coder-30b-a3b-instruct-fp8).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (lower for code)
            max_tokens: Maximum tokens in response
        
        Returns:
            Response content as string
        """
        self._rate_limit(self._last_coder_request, self._coder_interval)
        self._last_coder_request = time.time()
        
        response = self.client.chat.completions.create(
            model=self.coder_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512
    ):
        """
        Stream chat completion response.
        
        Yields chunks of response content.
        """
        self._rate_limit(self._last_chat_request, self._chat_interval)
        self._last_chat_request = time.time()
        
        stream = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for texts using bge-m3 model.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        self._rate_limit(self._last_embedding_request, self._embedding_interval)
        self._last_embedding_request = time.time()
        
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        
        return [item.embedding for item in response.data]


# Global client instance
scibox_client = SciBoxClient()


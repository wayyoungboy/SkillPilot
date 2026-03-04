"""Embedding Service for generating vector embeddings"""

from typing import Any

import httpx

from skillpilot.core.config import settings
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.

    Supports multiple embedding providers:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Local models (via sentence-transformers)
    - Mock (for development/testing without API keys)
    """

    def __init__(self):
        self.provider = settings.embedding_provider
        self.dimension = settings.seekdb_vector_dimension
        self._client = None
        self._http_client = None

    def _get_client(self) -> Any:
        """Get or create embedding client based on provider"""
        if self._client is None:
            if self.provider == "openai":
                try:
                    from openai import AsyncOpenAI

                    if not settings.openai_api_key:
                        raise ValueError("OPENAI_API_KEY not configured")

                    self._client = AsyncOpenAI(api_key=settings.openai_api_key)
                    logger.info("OpenAI embedding client initialized")
                except ImportError:
                    logger.error("OpenAI SDK not installed. Run: pip install openai")
                    raise
                except Exception as e:
                    logger.error("Failed to initialize OpenAI client", error=str(e))
                    raise

            elif self.provider == "local":
                try:
                    from sentence_transformers import SentenceTransformer

                    self._client = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("Local embedding model loaded")
                except ImportError:
                    logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
                    raise
                except Exception as e:
                    logger.error("Failed to load local embedding model", error=str(e))
                    raise

            # Mock provider doesn't need a client - generates dummy embeddings
            elif self.provider == "mock":
                logger.info("Mock embedding provider initialized (no API key required)")

        return self._client

    async def generate_embedding(self, text: str, max_retries: int = 3) -> list[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed
            max_retries: Maximum retry attempts for API failures

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If embedding fails after all retries
        """
        client = self._get_client()

        # Mock provider - return deterministic dummy embedding
        if self.provider == "mock":
            import hashlib
            # Use hash for deterministic "embeddings" based on input text
            hash_bytes = hashlib.sha256(text.encode()).digest()
            # Expand to desired dimension
            import random
            random.seed(int.from_bytes(hash_bytes[:4], 'big'))
            embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
            logger.debug("Mock embedding generated", dimension=len(embedding))
            return embedding

        for attempt in range(max_retries):
            try:
                if self.provider == "openai":
                    response = await client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text,
                        dimensions=self.dimension,
                    )
                    embedding = response.data[0].embedding
                    logger.debug("OpenAI embedding generated", dimension=len(embedding))
                    return embedding

                elif self.provider == "local":
                    # sentence-transformers is synchronous
                    embedding = client.encode(text, normalize_embeddings=True).tolist()
                    logger.debug("Local embedding generated", dimension=len(embedding))
                    return embedding

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    # Rate limit - wait and retry
                    import asyncio
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning("Rate limited, retrying in", seconds=wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("Embedding API HTTP error", status=e.response.status_code, error=str(e))
                raise
            except Exception as e:
                logger.error("Embedding generation failed", provider=self.provider, attempt=attempt + 1, error=str(e))
                if attempt == max_retries - 1:
                    raise
                import asyncio
                await asyncio.sleep(2 ** attempt)

        raise ValueError("Embedding generation failed after all retries")

    async def generate_embeddings_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
            logger.debug("Embedding batch processed", batch=i // batch_size + 1)

        return embeddings

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts"""
        client = self._get_client()

        try:
            if self.provider == "mock":
                # Generate mock embeddings for batch
                import hashlib
                import random
                embeddings = []
                for text in texts:
                    hash_bytes = hashlib.sha256(text.encode()).digest()
                    random.seed(int.from_bytes(hash_bytes[:4], 'big'))
                    embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
                    embeddings.append(embedding)
                return embeddings

            elif self.provider == "openai":
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts,
                    dimensions=self.dimension,
                )
                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                return [item.embedding for item in sorted_data]

            elif self.provider == "local":
                embeddings = client.encode(texts, normalize_embeddings=True, batch_size=len(texts))
                return embeddings.tolist()

        except Exception as e:
            logger.error("Batch embedding failed", error=str(e))
            raise

    def set_provider(self, provider: str) -> None:
        """
        Set the embedding provider.

        Args:
            provider: Provider name ('openai', 'local', 'mock')
        """
        if provider not in ["openai", "local", "mock"]:
            raise ValueError(f"Unknown provider: {provider}")

        self.provider = provider
        self._client = None  # Reset client to reinitialize with new provider
        logger.info("Embedding provider set", provider=provider)

    async def close(self) -> None:
        """Close HTTP client connections"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


embedding_service = EmbeddingService()

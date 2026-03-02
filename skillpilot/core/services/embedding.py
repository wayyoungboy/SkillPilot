"""Embedding Service for generating vector embeddings"""

from typing import Any

from skillpilot.core.config import settings
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Supports multiple embedding providers:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Local models (via sentence-transformers)
    - Custom embedding endpoints
    """

    def __init__(self):
        self.provider = "openai"  # Default provider
        self.dimension = settings.seekdb_vector_dimension
        self._client = None

    def _get_client(self) -> Any:
        """Get or create embedding client based on provider"""
        if self._client is None:
            if self.provider == "openai":
                try:
                    from openai import AsyncOpenAI

                    self._client = AsyncOpenAI()
                    logger.info("OpenAI embedding client initialized")
                except ImportError:
                    logger.warning("OpenAI not installed, using mock embeddings")
                    self._client = "mock"
            elif self.provider == "local":
                try:
                    from sentence_transformers import SentenceTransformer

                    self._client = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("Local embedding model loaded")
                except ImportError:
                    logger.warning("sentence-transformers not installed, using mock embeddings")
                    self._client = "mock"

        return self._client

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        client = self._get_client()

        if client == "mock":
            return self._generate_mock_embedding(text)

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
                # sentence-transformers is synchronous, run in executor if needed
                embedding = client.encode(text, normalize_embeddings=True).tolist()
                logger.debug("Local embedding generated", dimension=len(embedding))
                return embedding

        except Exception as e:
            logger.error("Embedding generation failed", provider=self.provider, error=str(e))
            # Fallback to mock embedding
            return self._generate_mock_embedding(text)

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

        if client == "mock":
            return [self._generate_mock_embedding(text) for text in texts]

        try:
            if self.provider == "openai":
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
            return [self._generate_mock_embedding(text) for text in texts]

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding for testing"""
        import hashlib

        # Create a deterministic hash-based embedding
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(self.dimension):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] + i) % 256 / 256.0
            embedding.append(value)

        return embedding

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


embedding_service = EmbeddingService()

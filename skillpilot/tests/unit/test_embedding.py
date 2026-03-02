"""Tests for Embedding Service"""

import pytest

from skillpilot.core.services.embedding import embedding_service


class TestEmbeddingService:
    """Test embedding service functionality"""

    @pytest.mark.asyncio
    async def test_generate_embedding_mock(self):
        """Test embedding generation in mock mode"""
        # Ensure mock mode
        embedding_service.set_provider("mock")
        
        text = "This is a test skill description"
        embedding = await embedding_service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_generate_embedding_deterministic(self):
        """Test that embeddings are deterministic for same input"""
        embedding_service.set_provider("mock")
        
        text = "Test text for embedding"
        embedding1 = await embedding_service.generate_embedding(text)
        embedding2 = await embedding_service.generate_embedding(text)
        
        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_generate_embedding_different(self):
        """Test that different texts produce different embeddings"""
        embedding_service.set_provider("mock")
        
        text1 = "First text"
        text2 = "Second text"
        
        embedding1 = await embedding_service.generate_embedding(text1)
        embedding2 = await embedding_service.generate_embedding(text2)
        
        assert embedding1 != embedding2

    @pytest.mark.asyncio
    async def test_batch_embedding(self):
        """Test batch embedding generation"""
        embedding_service.set_provider("mock")
        
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = await embedding_service.generate_embeddings_batch(texts)
        
        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings)

    @pytest.mark.asyncio
    async def test_provider_switching(self):
        """Test switching between providers"""
        embedding_service.set_provider("mock")
        assert embedding_service.provider == "mock"
        
        embedding_service.set_provider("openai")
        assert embedding_service.provider == "openai"
        
        # Reset to mock for other tests
        embedding_service.set_provider("mock")

    @pytest.mark.asyncio
    async def test_invalid_provider(self):
        """Test that invalid provider raises error"""
        with pytest.raises(ValueError, match="Unknown provider"):
            embedding_service.set_provider("invalid_provider")

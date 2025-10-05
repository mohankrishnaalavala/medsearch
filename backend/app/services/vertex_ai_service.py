"""Vertex AI service for embeddings and chat completion."""

import logging
import os
from typing import List, Optional

import vertexai
from google.auth import default
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class VertexAIService:
    """Service for Vertex AI operations."""

    def __init__(self) -> None:
        """Initialize Vertex AI service."""
        self.embedding_model: Optional[TextEmbeddingModel] = None
        self.chat_model: Optional[GenerativeModel] = None
        self.chat_escalation_model: Optional[GenerativeModel] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize Vertex AI and load models."""
        try:
            # Load credentials from service account key file
            credentials = None
            credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS

            if credentials_path and os.path.exists(credentials_path):
                logger.info(f"Loading credentials from: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            else:
                logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS not set or file not found at {credentials_path}, using default credentials")
                credentials, _ = default()

            # Initialize Vertex AI with explicit credentials
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.VERTEX_AI_LOCATION,
                credentials=credentials,
            )

            # Load embedding model
            self.embedding_model = TextEmbeddingModel.from_pretrained(
                settings.VERTEX_AI_EMBEDDING_MODEL
            )

            # Load chat models
            self.chat_model = GenerativeModel(settings.VERTEX_AI_CHAT_MODEL)
            self.chat_escalation_model = GenerativeModel(
                settings.VERTEX_AI_CHAT_ESCALATION_MODEL
            )

            self._initialized = True
            logger.info("Vertex AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    async def generate_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            task_type: Task type for embedding (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)

        Returns:
            Embedding vector
        """
        if not self._initialized:
            self.initialize()

        try:
            # Create embedding input
            embedding_input = TextEmbeddingInput(text=text, task_type=task_type)

            # Generate embedding
            embeddings = self.embedding_model.get_embeddings([embedding_input])

            if not embeddings or not embeddings[0].values:
                raise ValueError("Failed to generate embedding")

            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embeddings[0].values

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(
        self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            task_type: Task type for embedding

        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            self.initialize()

        try:
            # Create embedding inputs
            embedding_inputs = [
                TextEmbeddingInput(text=text, task_type=task_type) for text in texts
            ]

            # Generate embeddings
            embeddings = self.embedding_model.get_embeddings(embedding_inputs)

            if not embeddings:
                raise ValueError("Failed to generate embeddings")

            logger.info(f"Generated {len(embeddings)} embeddings")
            return [emb.values for emb in embeddings]

        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            raise

    async def generate_chat_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        use_escalation: bool = False,
    ) -> str:
        """
        Generate chat response using Gemini.

        Args:
            prompt: User prompt
            system_instruction: System instruction for the model
            temperature: Sampling temperature (0-1)
            max_output_tokens: Maximum tokens to generate
            use_escalation: Whether to use escalation model (Pro instead of Flash)

        Returns:
            Generated response text
        """
        if not self._initialized:
            self.initialize()

        try:
            # Select model
            model = self.chat_escalation_model if use_escalation else self.chat_model

            # Configure generation
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }

            # Generate response
            # Prepend system instruction to prompt if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"

            response = model.generate_content(
                full_prompt, generation_config=generation_config
            )

            if not response or not response.text:
                raise ValueError("Failed to generate response")

            model_name = (
                settings.VERTEX_AI_CHAT_ESCALATION_MODEL
                if use_escalation
                else settings.VERTEX_AI_CHAT_MODEL
            )
            logger.info(f"Generated chat response using {model_name}")
            return response.text

        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise

    async def generate_streaming_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        use_escalation: bool = False,
    ):
        """
        Generate streaming chat response.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens
            use_escalation: Use escalation model

        Yields:
            Response chunks
        """
        if not self._initialized:
            self.initialize()

        try:
            # Select model
            model = self.chat_escalation_model if use_escalation else self.chat_model

            # Configure generation
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }

            # Generate streaming response
            if system_instruction:
                responses = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    system_instruction=system_instruction,
                    stream=True,
                )
            else:
                responses = model.generate_content(
                    prompt, generation_config=generation_config, stream=True
                )

            for chunk in responses:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            raise

    async def health_check(self) -> dict:
        """Check Vertex AI service health."""
        try:
            if not self._initialized:
                self.initialize()

            # Test embedding generation
            test_embedding = await self.generate_embedding("test", "RETRIEVAL_QUERY")

            if test_embedding and len(test_embedding) == 768:
                return {
                    "status": "up",
                    "embedding_model": settings.VERTEX_AI_EMBEDDING_MODEL,
                    "chat_model": settings.VERTEX_AI_CHAT_MODEL,
                }
            else:
                return {"status": "degraded", "message": "Embedding test failed"}

        except Exception as e:
            logger.error(f"Vertex AI health check failed: {e}")
            return {"status": "down", "message": str(e)}


# Global Vertex AI service instance
_vertex_ai_service: Optional[VertexAIService] = None


def get_vertex_ai_service() -> VertexAIService:
    """Get global Vertex AI service instance."""
    global _vertex_ai_service
    if _vertex_ai_service is None:
        _vertex_ai_service = VertexAIService()
        _vertex_ai_service.initialize()
    return _vertex_ai_service


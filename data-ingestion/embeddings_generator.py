"""Embedding generation service using Vertex AI."""

import asyncio
import logging
import os
from typing import List, Optional

from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using Vertex AI."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-embedding-004",
        batch_size: int = 5,
    ) -> None:
        """
        Initialize embedding generator.

        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location
            model_name: Embedding model name
            batch_size: Number of texts to process in one batch
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.batch_size = batch_size
        self.model: Optional[TextEmbeddingModel] = None

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        logger.info(f"Initialized Vertex AI for project {project_id}")

    def initialize(self) -> None:
        """Initialize the embedding model."""
        if self.model is None:
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")

    async def generate_embedding(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            task_type: Task type for embedding

        Returns:
            Embedding vector
        """
        if not self.model:
            self.initialize()

        try:
            # Truncate text if too long (max 20,000 characters)
            text = text[:20000]

            embedding_input = TextEmbeddingInput(text=text, task_type=task_type)
            embeddings = self.model.get_embeddings([embedding_input])

            if not embeddings or not embeddings[0].values:
                raise ValueError("Failed to generate embedding")

            return embeddings[0].values

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(
        self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            task_type: Task type for embedding

        Returns:
            List of embedding vectors
        """
        if not self.model:
            self.initialize()

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            try:
                # Truncate texts if too long
                batch = [text[:20000] for text in batch]

                # Create embedding inputs
                embedding_inputs = [
                    TextEmbeddingInput(text=text, task_type=task_type) for text in batch
                ]

                # Generate embeddings
                embeddings = self.model.get_embeddings(embedding_inputs)

                # Extract values
                batch_embeddings = [emb.values for emb in embeddings]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i // self.batch_size + 1}")

                # Rate limiting: sleep between batches
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                # Add empty embeddings for failed batch
                all_embeddings.extend([[0.0] * 768 for _ in batch])

        return all_embeddings

    def generate_embedding_sync(
        self, text: str, task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[float]:
        """
        Generate embedding synchronously.

        Args:
            text: Text to embed
            task_type: Task type for embedding

        Returns:
            Embedding vector
        """
        if not self.model:
            self.initialize()

        try:
            # Truncate text if too long
            text = text[:20000]

            embedding_input = TextEmbeddingInput(text=text, task_type=task_type)
            embeddings = self.model.get_embeddings([embedding_input])

            if not embeddings or not embeddings[0].values:
                raise ValueError("Failed to generate embedding")

            return embeddings[0].values

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector on error
            return [0.0] * 768

    def generate_embeddings_batch_sync(
        self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts synchronously.

        Args:
            texts: List of texts to embed
            task_type: Task type for embedding

        Returns:
            List of embedding vectors
        """
        if not self.model:
            self.initialize()

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            try:
                # Truncate texts if too long
                batch = [text[:20000] for text in batch]

                # Create embedding inputs
                embedding_inputs = [
                    TextEmbeddingInput(text=text, task_type=task_type) for text in batch
                ]

                # Generate embeddings
                embeddings = self.model.get_embeddings(embedding_inputs)

                # Extract values
                batch_embeddings = [emb.values for emb in embeddings]
                all_embeddings.extend(batch_embeddings)

                logger.info(
                    f"Generated embeddings for batch {i // self.batch_size + 1} "
                    f"({len(batch_embeddings)} embeddings)"
                )

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                # Add zero vectors for failed batch
                all_embeddings.extend([[0.0] * 768 for _ in batch])

        return all_embeddings


def get_embedding_generator(
    project_id: Optional[str] = None,
    location: str = "us-central1",
    model_name: str = "text-embedding-004",
) -> EmbeddingGenerator:
    """
    Get embedding generator instance.

    Args:
        project_id: Google Cloud project ID (defaults to env var)
        location: Vertex AI location
        model_name: Embedding model name

    Returns:
        EmbeddingGenerator instance
    """
    if project_id is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "medsearch-ai")

    return EmbeddingGenerator(
        project_id=project_id, location=location, model_name=model_name
    )


# Example usage
if __name__ == "__main__":
    # Test embedding generation
    generator = get_embedding_generator()
    generator.initialize()

    # Test single embedding
    text = "Diabetes is a chronic disease that affects how your body processes blood sugar."
    embedding = generator.generate_embedding_sync(text)
    print(f"Generated embedding with {len(embedding)} dimensions")

    # Test batch embeddings
    texts = [
        "Hypertension is high blood pressure.",
        "Cancer is a group of diseases involving abnormal cell growth.",
        "Alzheimer's disease is a progressive neurological disorder.",
    ]
    embeddings = generator.generate_embeddings_batch_sync(texts)
    print(f"Generated {len(embeddings)} embeddings")


"""Vertex AI service for embeddings and chat completion."""

import logging
import os
from typing import Any, Dict, List, Optional

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

    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        text_fields: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Optionally re-rank results using a single per-call Gemini scoring.

        This uses the chat model (Flash/Pro) to assign a relevance score 0.0-1.0 to
        each candidate relative to the query, then sorts by that score. To control
        cost, we (a) truncate content, (b) score up to top_k items in one call.
        """
        if not self._initialized:
            self.initialize()

        if not results:
            return results

        try:
            fields = text_fields or [
                "abstract",
                "description",
                "brief_summary",
                "detailed_description",
                "indications",
                "warnings",
            ]
            k = max(1, min(len(results), top_k or settings.VERTEX_AI_RERANK_TOP_K))
            subset = results[:k]

            # Prepare compact items
            serializable: List[Dict[str, str]] = []
            for r in subset:
                rid = str(r.get("id") or r.get("_id") or "")
                title = str(r.get("title") or r.get("drug_name") or "")
                text = ""
                for f in fields:
                    val = r.get(f)
                    if val:
                        text = str(val)
                        break
                if not text:
                    # fallback to any long-ish string fields
                    for f, v in r.items():
                        if isinstance(v, str) and len(v) > 50:
                            text = v
                            break
                # Truncate to control tokens
                text = text[:600]
                serializable.append({"id": rid, "title": title[:120], "text": text})

            instruction = (
                "You are a strict scoring function. For the given user query, score each item "
                "for relevance between 0.0 and 1.0 (float). Return ONLY a JSON array with objects "
                "{\"id\": string, \"score\": number}. No extra text."
            )
            numbered_items = []
            for i, it in enumerate(serializable, start=1):
                numbered_items.append(
                    f"{i}. id={it['id']}\nTitle: {it['title']}\nText: {it['text']}"
                )
            prompt = (
                f"Query: {query}\n\n{instruction}\n\nItems to score:\n" + "\n\n".join(numbered_items)
            )

            generation_config = {
                "temperature": 0.0,
                "max_output_tokens": 512,
                "top_p": 0.9,
                "top_k": 40,
            }

            model = self.chat_model
            response = model.generate_content(prompt, generation_config=generation_config)
            raw = (response.text or "").strip()

            # Extract JSON array
            import json as _json

            def _extract_json_array(s: str) -> str:
                lb = s.find("[")
                rb = s.rfind("]")
                if lb != -1 and rb != -1 and rb > lb:
                    return s[lb : rb + 1]
                return s

            payload = _extract_json_array(raw)
            scored = _json.loads(payload)
            score_map = {str(e.get("id")): float(e.get("score", 0.0)) for e in scored if e}

            # Merge back into results
            out = []
            for r in results:
                rid = str(r.get("id") or r.get("_id") or "")
                r_copy = dict(r)
                r_copy["rerank_score"] = score_map.get(rid, r_copy.get("relevance_score", 0.0))
                out.append(r_copy)
            out.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return out
        except Exception as e:
            logger.warning(f"Rerank failed, returning original order: {e}")
            return results

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


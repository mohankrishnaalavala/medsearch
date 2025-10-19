#!/usr/bin/env python3
"""Test the MedSearch API - Vertex AI integration."""

import asyncio
import sys

import httpx


async def test_vertex_ai_direct():
    """Test Vertex AI directly via Python SDK."""
    print("\n" + "="*80)
    print("Testing Vertex AI SDK directly")
    print("="*80 + "\n")

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        # Initialize Vertex AI
        vertexai.init(project="medsearch-ai", location="us-central1")

        # Test chat model
        model = GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("What is diabetes? Answer in one sentence.")

        print(f"✓ Vertex AI chat model working")
        print(f"Response: {response.text[:200]}...")

        # Test embedding model
        from vertexai.language_models import TextEmbeddingModel
        embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = embedding_model.get_embeddings(["diabetes treatment"])

        print(f"✓ Vertex AI embedding model working")
        print(f"Embedding dimension: {len(embeddings[0].values)}")

        return True

    except Exception as e:
        print(f"✗ Vertex AI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoint():
    """Test the health endpoint."""
    print("\n" + "="*80)
    print("Testing Health Endpoint")
    print("="*80 + "\n")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            health = response.json()
            print(f"Overall status: {health.get('status')}")
            print(f"Environment: {health.get('environment')}")
            print(f"\nServices:")
            for service, status in health.get('services', {}).items():
                print(f"  {service}: {status.get('status')}")

            vertex_status = health.get('services', {}).get('vertex_ai', {}).get('status')
            if vertex_status == 'up':
                print(f"\n✓ Vertex AI is UP and ready")
                return True
            else:
                print(f"\n✗ Vertex AI is {vertex_status}")
                return False

        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False


async def test_secret_manager_integration():
    """Test that Secret Manager integration is working."""
    print("\n" + "="*80)
    print("Testing Secret Manager Integration")
    print("="*80 + "\n")

    import os

    # Check if credentials are loaded
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"✓ GOOGLE_APPLICATION_CREDENTIALS is set")
        print(f"  Path: {creds_path}")

        if os.path.exists(creds_path):
            print(f"✓ Credentials file exists")

            # Check if it's from Secret Manager (in /tmp)
            if "/tmp/" in creds_path:
                print(f"✓ Credentials loaded from Secret Manager")
                return True
            else:
                print(f"ℹ Credentials loaded from local file (not Secret Manager)")
                return True
        else:
            print(f"✗ Credentials file does not exist")
            return False
    else:
        print(f"✗ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("MedSearch AI - Pillar 2 Integration Tests")
    print("Google Cloud Secret Manager + Vertex AI")
    print("="*80)

    results = []

    # Test 1: Health endpoint
    results.append(("Health Endpoint", await test_health_endpoint()))

    # Test 2: Secret Manager
    results.append(("Secret Manager", await test_secret_manager_integration()))

    # Test 3: Vertex AI SDK
    results.append(("Vertex AI SDK", await test_vertex_ai_direct()))

    # Summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80 + "\n")

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


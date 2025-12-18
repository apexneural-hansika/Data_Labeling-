"""
Test HuggingFace embedding generation
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedding_providers import HuggingFaceEmbeddingProvider, create_embedding_provider
from utils.database import EmbeddingDatabase
from config import Config

print("=" * 60)
print("Testing HuggingFace Embedding Generation")
print("=" * 60)

# Test 1: Direct provider
print("\n[1/3] Testing HuggingFace Provider Directly...")
try:
    provider = HuggingFaceEmbeddingProvider()
    if provider.model:
        test_text = "This is a test document for embedding generation."
        embedding = provider.generate_embedding(test_text)
        
        if embedding:
            print(f"[OK] Embedding generated successfully!")
            print(f"  - Text: {test_text[:50]}...")
            print(f"  - Dimensions: {len(embedding)}")
            print(f"  - First 5 values: {embedding[:5]}")
            print(f"  - Model: {provider.model_name}")
        else:
            print("[ERROR] Failed to generate embedding")
    else:
        print("[ERROR] Model not loaded")
except Exception as e:
    print(f"[ERROR] Provider test failed: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 2: Auto provider selection
print("\n[2/3] Testing Auto Provider Selection...")
try:
    provider = create_embedding_provider(provider_type='auto')
    if provider:
        print(f"[OK] Provider created: {type(provider).__name__}")
        test_text = "Golden Retriever puppies playing in a garden."
        embedding = provider.generate_embedding(test_text)
        
        if embedding:
            print(f"[OK] Embedding generated!")
            print(f"  - Dimensions: {len(embedding)}")
        else:
            print("[ERROR] Failed to generate embedding")
    else:
        print("[ERROR] No provider available")
except Exception as e:
    print(f"[ERROR] Auto provider test failed: {str(e)}")

# Test 3: Database integration
print("\n[3/3] Testing Database Integration...")
try:
    # Force HuggingFace provider
    db = EmbeddingDatabase(
        connection_string=Config.SUPABASE_DB_URL,
        embedding_provider_type='huggingface'
    )
    
    if db.embedding_provider:
        print(f"[OK] Database initialized with HuggingFace provider")
        print(f"  - Embedding dimension: {db.embedding_dimension}")
        
        test_text = "Image of Golden Retriever puppies with detailed labels and metadata."
        embedding = db.generate_embedding(test_text)
        
        if embedding:
            print(f"[OK] Embedding generated via database!")
            print(f"  - Dimensions: {len(embedding)}")
            print(f"  - Expected: {db.embedding_dimension}")
            
            if len(embedding) == db.embedding_dimension:
                print("[SUCCESS] Dimension matches expected value!")
            else:
                print(f"[WARNING] Dimension mismatch: got {len(embedding)}, expected {db.embedding_dimension}")
        else:
            print("[ERROR] Failed to generate embedding")
    else:
        print("[ERROR] Embedding provider not initialized")
    
    db.close()
    
except Exception as e:
    print(f"[ERROR] Database integration test failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nTo use HuggingFace embeddings, set in .env:")
print("  EMBEDDING_PROVIDER=huggingface")
print("=" * 60)


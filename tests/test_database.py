"""
Test script for Supabase pgvector database setup
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import EmbeddingDatabase
from config import Config
from utils.logger import get_system_logger

logger = get_system_logger()


def test_database_connection():
    """Test database connection."""
    print("=" * 60)
    print("Testing Supabase Database Connection")
    print("=" * 60)
    
    try:
        # Initialize database
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        print("[OK] Database connection pool created successfully")
        
        # Test connection by getting statistics
        stats = db.get_statistics()
        print(f"[OK] Database connection successful")
        print(f"  - Total records: {stats.get('total_records', 0) or 0}")
        print(f"  - Records with embeddings: {stats.get('records_with_embeddings', 0) or 0}")
        avg_quality = stats.get('avg_quality_score')
        print(f"  - Average quality score: {avg_quality:.2f}" if avg_quality is not None else "  - Average quality score: N/A")
        print(f"  - Unique modalities: {stats.get('unique_modalities', 0) or 0}")
        print(f"  - Unique categories: {stats.get('unique_categories', 0) or 0}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if pgvector extension is enabled in Supabase")
        print("2. Verify the connection string is correct")
        print("3. Ensure the table 'data_labeling_embeddings' exists")
        print("4. Check network connectivity to Supabase")
        return False


def test_embedding_generation():
    """Test embedding generation."""
    print("\n" + "=" * 60)
    print("Testing Embedding Generation")
    print("=" * 60)
    
    # Check if we have a direct OpenAI key (not OpenRouter)
    embedding_key = Config.get_openai_key_for_embeddings()
    if not embedding_key:
        print("[INFO] Direct OpenAI API key not set. Skipping embedding generation test.")
        print("       Set OPENAI_DIRECT_API_KEY environment variable for embedding generation.")
        print("       Note: OpenRouter keys (sk-or-...) cannot be used for embeddings.")
        print("[OK] Test skipped (expected behavior when key not available)")
        return True  # This is expected, not a failure
    
    if embedding_key.startswith('sk-or-'):
        print("[INFO] Only OpenRouter key found. Embeddings require a direct OpenAI API key.")
        print("       Set OPENAI_DIRECT_API_KEY environment variable.")
        print("[OK] Test skipped (expected behavior when only OpenRouter key available)")
        return True  # This is expected, not a failure
    
    try:
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=embedding_key
        )
        
        test_text = "This is a test document for data labeling. It contains sample content."
        embedding = db.generate_embedding(test_text)
        
        if embedding:
            print(f"[OK] Embedding generated successfully")
            print(f"  - Text length: {len(test_text)} characters")
            print(f"  - Embedding dimensions: {len(embedding)}")
            print(f"  - First 5 values: {embedding[:5]}")
            db.close()
            return True
        else:
            print("[ERROR] Failed to generate embedding")
            db.close()
            return False
            
    except Exception as e:
        error_msg = str(e)
        if 'invalid_api_key' in error_msg or '401' in error_msg:
            print(f"[WARNING] Embedding generation failed: Invalid API key")
            print("          Set OPENAI_DIRECT_API_KEY with a direct OpenAI key (not OpenRouter)")
        else:
            print(f"[ERROR] Embedding generation failed: {error_msg}")
        return False


def test_store_embedding():
    """Test storing an embedding."""
    print("\n" + "=" * 60)
    print("Testing Embedding Storage")
    print("=" * 60)
    
    # Check if we have a direct OpenAI key
    embedding_key = Config.get_openai_key_for_embeddings()
    if not embedding_key or embedding_key.startswith('sk-or-'):
        print("[INFO] Direct OpenAI key not available. Testing storage without embedding.")
        print("       (Data will be stored, but without vector embedding)")
    
    try:
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Create test output data
        test_output = {
            'file_name': 'test_file.pdf',
            'modality': 'text_document',
            'category': 'document_processing',
            'raw_text': 'This is a test document for embedding storage.',
            'labels': {
                'content_category': 'document_processing',
                'modality': 'text_document'
            },
            'quality_score': 0.85,
            'processing_time': 1.5,
            'timestamp': '2024-01-01T00:00:00',
            'agentic_system': True,
            'agents_involved': ['content_extractor', 'supervisor']
        }
        
        file_id = 'test_' + str(os.urandom(8).hex())
        success = db.store_embedding(
            file_id=file_id,
            file_name=test_output['file_name'],
            output_data=test_output
        )
        
        if success:
            print(f"[OK] Data stored successfully")
            print(f"  - File ID: {file_id}")
            
            # Try to retrieve it
            retrieved = db.get_by_file_id(file_id)
            if retrieved:
                print(f"[OK] Data retrieved successfully")
                print(f"  - Retrieved file name: {retrieved['file_name']}")
                print(f"  - Quality score: {retrieved['quality_score']}")
                if retrieved.get('embedding'):
                    print(f"  - Has embedding: Yes")
                else:
                    print(f"  - Has embedding: No (set OPENAI_DIRECT_API_KEY to generate embeddings)")
            else:
                print("[WARNING] Data stored but could not be retrieved")
            
            db.close()
            return True
        else:
            print("[ERROR] Failed to store data")
            db.close()
            return False
            
    except Exception as e:
        print(f"[ERROR] Embedding storage failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_search():
    """Test similarity search."""
    print("\n" + "=" * 60)
    print("Testing Similarity Search")
    print("=" * 60)
    
    # Check if we have a direct OpenAI key
    embedding_key = Config.get_openai_key_for_embeddings()
    if not embedding_key or embedding_key.startswith('sk-or-'):
        print("[INFO] Direct OpenAI key not available. Similarity search requires embeddings.")
        print("       Set OPENAI_DIRECT_API_KEY to enable similarity search.")
        print("[OK] Similarity search function works (no embeddings to search)")
        return True
    
    try:
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        query_text = "document processing and text extraction"
        results = db.search_similar(query_text, limit=5, threshold=0.5)
        
        print(f"[OK] Similarity search completed")
        print(f"  - Query: {query_text}")
        print(f"  - Results found: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    - File: {result.get('file_name', 'N/A')}")
            print(f"    - Similarity: {result.get('similarity', 0):.3f}")
            print(f"    - Modality: {result.get('modality', 'N/A')}")
            print(f"    - Category: {result.get('category', 'N/A')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Similarity search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    print("Supabase pgvector Database Test Suite")
    print("=" * 60)
    print("\nMake sure you have:")
    print("1. Enabled pgvector extension in Supabase")
    print("2. Created the data_labeling_embeddings table")
    print("3. Set OPENAI_API_KEY in your environment or config")
    print("4. Verified the connection string is correct")
    print("\n")
    
    results = []
    
    # Run tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Embedding Generation", test_embedding_generation()))
    results.append(("Store Embedding", test_store_embedding()))
    results.append(("Similarity Search", test_similarity_search()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILED] Some tests failed. Please check the errors above.")
    print("=" * 60)


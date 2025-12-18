"""
Test script to process an image and store it with embeddings
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator_agentic import AgenticOrchestrator
from config import Config
from utils.database import EmbeddingDatabase
from utils.logger import get_system_logger

logger = get_system_logger()


def test_image_embedding(image_path: str):
    """Process an image and store it with embeddings."""
    print("=" * 60)
    print("Testing Image Processing with Embedding Storage")
    print("=" * 60)
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return False
    
    print(f"\n[1/4] Processing image: {os.path.basename(image_path)}")
    
    try:
        # Initialize orchestrator
        orchestrator = AgenticOrchestrator(
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Process the image
        print("[2/4] Extracting content and generating labels...")
        result = orchestrator.process_file(
            file_path=image_path,
            output_dir='output'
        )
        
        if not result.get('success', False):
            print(f"[ERROR] Image processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("[OK] Image processed successfully")
        print(f"  - Modality: {result.get('modality', 'N/A')}")
        print(f"  - Category: {result.get('category', 'N/A')}")
        print(f"  - Quality Score: {result.get('quality_score', 0):.2f}")
        print(f"  - Processing Time: {result.get('processing_time', 0):.2f}s")
        
        # Check if embedding was stored
        print("\n[3/4] Checking embedding storage...")
        
        if orchestrator.embedding_db:
            # Get file_id from result
            file_id = result.get('file_id') or os.path.splitext(
                os.path.basename(image_path)
            )[0]
            
            # Try to retrieve from database
            stored_record = orchestrator.embedding_db.get_by_file_id(file_id)
            
            if stored_record:
                print("[OK] Record found in database")
                print(f"  - File ID: {stored_record['file_id']}")
                print(f"  - File Name: {stored_record['file_name']}")
                print(f"  - Has Embedding: {'Yes' if stored_record.get('embedding') else 'No'}")
                print(f"  - Quality Score: {stored_record.get('quality_score', 'N/A')}")
                
                if stored_record.get('embedding'):
                    print(f"  - Embedding Dimensions: {len(stored_record['embedding'])}")
                    print("[SUCCESS] Image processed and stored with embedding!")
                else:
                    print("[INFO] Image stored but without embedding (direct OpenAI key needed)")
            else:
                print("[WARNING] Record not found in database (may have been stored with different ID)")
        else:
            print("[WARNING] Embedding database not initialized")
        
        # Show some extracted content
        print("\n[4/4] Extracted Content Preview:")
        print("-" * 60)
        raw_text = result.get('raw_text', '')
        if raw_text:
            preview = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
            print(preview)
        else:
            print("(No text content extracted)")
        
        # Show labels
        labels = result.get('labels', {})
        if labels:
            print("\nLabels:")
            for key, value in labels.items():
                if isinstance(value, dict):
                    print(f"  - {key}:")
                    for k, v in value.items():
                        print(f"    - {k}: {v}")
                else:
                    print(f"  - {key}: {value}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Test completed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_search():
    """Test searching for similar images."""
    print("\n" + "=" * 60)
    print("Testing Similarity Search for Images")
    print("=" * 60)
    
    # Check if we have a direct OpenAI key
    embedding_key = Config.get_openai_key_for_embeddings()
    if not embedding_key or embedding_key.startswith('sk-or-'):
        print("[INFO] Direct OpenAI key not available. Skipping similarity search.")
        print("       Set OPENAI_DIRECT_API_KEY to enable similarity search.")
        return True
    
    try:
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=embedding_key
        )
        
        # Search for images
        query = "chemical reaction scheme or diagram"
        results = db.search_similar(
            query_text=query,
            limit=5,
            threshold=0.5,
            modality="image"
        )
        
        print(f"[OK] Similarity search completed")
        print(f"  - Query: {query}")
        print(f"  - Results found: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    - File: {result.get('file_name', 'N/A')}")
            print(f"    - Similarity: {result.get('similarity', 0):.3f}")
            print(f"    - Category: {result.get('category', 'N/A')}")
            print(f"    - Quality: {result.get('quality_score', 'N/A')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Similarity search failed: {str(e)}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test image processing with embeddings')
    parser.add_argument(
        'image_path',
        nargs='?',
        default='test_data/reactions/310000688522.png',
        help='Path to image file to process'
    )
    parser.add_argument(
        '--search',
        action='store_true',
        help='Also test similarity search'
    )
    
    args = parser.parse_args()
    
    print("\n")
    print("Image Embedding Test")
    print("=" * 60)
    print(f"\nImage: {args.image_path}")
    print(f"OpenAI API Key: {'Set' if Config.OPENAI_API_KEY else 'Not Set'}")
    embedding_key = Config.get_openai_key_for_embeddings()
    print(f"Direct OpenAI Key for Embeddings: {'Set' if embedding_key and not embedding_key.startswith('sk-or-') else 'Not Set (will store without embedding)'}")
    print("\n")
    
    # Process image
    success = test_image_embedding(args.image_path)
    
    # Test similarity search if requested
    if args.search and success:
        test_similarity_search()
    
    sys.exit(0 if success else 1)


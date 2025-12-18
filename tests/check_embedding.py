"""
Script to check if embeddings were actually generated and stored
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import EmbeddingDatabase
from config import Config
import psycopg2

def check_embedding(file_id: str = '310000688522'):
    """Check if embedding exists for a file."""
    print("=" * 60)
    print("Checking Embedding Status")
    print("=" * 60)
    
    # Check API key status
    print("\n[1/3] Checking API Key Configuration...")
    embedding_key = Config.get_openai_key_for_embeddings()
    
    if not embedding_key:
        print("[WARNING] No OpenAI API key found")
        print("          Set OPENAI_DIRECT_API_KEY to generate embeddings")
    elif embedding_key.startswith('sk-or-'):
        print("[WARNING] Only OpenRouter key found (sk-or-...)")
        print("          Embeddings require a direct OpenAI key (sk-...)")
        print("          Set OPENAI_DIRECT_API_KEY with a direct OpenAI key")
    else:
        print(f"[OK] Direct OpenAI key found (starts with: {embedding_key[:7]}...)")
        print("      Embeddings can be generated")
    
    # Connect to database and check directly
    print("\n[2/3] Checking Database Record...")
    try:
        conn = psycopg2.connect(Config.SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Query the record
        cursor.execute("""
            SELECT 
                file_id,
                file_name,
                modality,
                category,
                CASE 
                    WHEN embedding IS NULL THEN 'NULL'
                    ELSE 'EXISTS'
                END as embedding_status,
                pg_typeof(embedding) as embedding_type,
                CASE 
                    WHEN embedding IS NOT NULL THEN (SELECT array_length(string_to_array(embedding::text, ','), 1))
                    ELSE NULL
                END as embedding_dimensions,
                quality_score,
                created_at
            FROM data_labeling_embeddings
            WHERE file_id = %s
        """, (file_id,))
        
        result = cursor.fetchone()
        
        if result:
            print(f"[OK] Record found for file_id: {file_id}")
            print(f"\nRecord Details:")
            print(f"  - File Name: {result[1]}")
            print(f"  - Modality: {result[2]}")
            print(f"  - Category: {result[3]}")
            print(f"  - Embedding Status: {result[4]}")
            print(f"  - Embedding Type: {result[5]}")
            print(f"  - Embedding Dimensions: {result[6] if result[6] else 'N/A'}")
            print(f"  - Quality Score: {result[7]}")
            print(f"  - Created At: {result[8]}")
            
            if result[4] == 'EXISTS' and result[6]:
                print(f"\n[SUCCESS] Embedding EXISTS!")
                print(f"  - Dimensions: {result[6]}")
                print(f"  - Type: {result[5]}")
                
                # Get a sample of the embedding values
                try:
                    cursor.execute("""
                        SELECT 
                            (embedding::text::float[])[1:5] as sample_values
                        FROM data_labeling_embeddings
                        WHERE file_id = %s AND embedding IS NOT NULL
                    """, (file_id,))
                    sample = cursor.fetchone()
                    if sample and sample[0]:
                        print(f"  - First 5 values: {sample[0]}")
                except Exception as e:
                    print(f"  - Could not extract sample values: {str(e)}")
            elif result[4] == 'NULL':
                print(f"\n[INFO] Embedding is NULL (not generated)")
                print("       This is expected if OPENAI_DIRECT_API_KEY is not set")
            else:
                print(f"\n[INFO] Embedding status: {result[4]}")
        else:
            print(f"[ERROR] No record found for file_id: {file_id}")
            print("\nChecking all records in database...")
            cursor.execute("""
                SELECT file_id, file_name, 
                       CASE WHEN embedding IS NULL THEN 'NO' ELSE 'YES' END as has_embedding
                FROM data_labeling_embeddings
                ORDER BY created_at DESC
                LIMIT 10
            """)
            records = cursor.fetchall()
            if records:
                print(f"\nFound {len(records)} recent records:")
                for rec in records:
                    print(f"  - {rec[0]}: {rec[1]} - Embedding: {rec[2]}")
            else:
                print("  No records found in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Database query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check using the database module
    print("\n[3/3] Checking via Database Module...")
    try:
        db = EmbeddingDatabase(
            connection_string=Config.SUPABASE_DB_URL,
            openai_api_key=embedding_key
        )
        
        record = db.get_by_file_id(file_id)
        if record:
            print(f"[OK] Record retrieved via module")
            if record.get('embedding'):
                print(f"[SUCCESS] Embedding found in record!")
                print(f"  - Type: {type(record['embedding'])}")
                if isinstance(record['embedding'], list):
                    print(f"  - Dimensions: {len(record['embedding'])}")
                    print(f"  - First 5 values: {record['embedding'][:5]}")
            else:
                print(f"[INFO] No embedding in record (field is None or missing)")
        else:
            print(f"[ERROR] Record not found via module")
        
        db.close()
        
    except Exception as e:
        print(f"[ERROR] Module check failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if result and result[4] == 'EXISTS':
        print("[SUCCESS] Embedding was generated and stored!")
    else:
        print("[INFO] Embedding was NOT generated")
        print("\nTo enable embeddings:")
        print("1. Set OPENAI_DIRECT_API_KEY environment variable")
        print("2. Use a direct OpenAI key (not OpenRouter)")
        print("3. Re-process the image or any new images")
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Check if embedding exists for a file')
    parser.add_argument(
        'file_id',
        nargs='?',
        default='310000688522',
        help='File ID to check'
    )
    
    args = parser.parse_args()
    
    check_embedding(args.file_id)


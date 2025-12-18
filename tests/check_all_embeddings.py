"""
Script to check all embeddings stored in Supabase database
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import EmbeddingDatabase
from config import Config
import psycopg2

def check_all_embeddings():
    """Check all embeddings in the database."""
    print("=" * 60)
    print("Checking All Embeddings in Supabase Database")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(Config.SUPABASE_DB_URL)
        cursor = conn.cursor()
        
        # Get all records
        cursor.execute("""
            SELECT 
                file_id,
                file_name,
                file_path,
                modality,
                category,
                CASE 
                    WHEN embedding IS NULL THEN 'NO'
                    ELSE 'YES'
                END as has_embedding,
                CASE 
                    WHEN embedding IS NOT NULL THEN 1536
                    ELSE NULL
                END as embedding_dimensions,
                quality_score,
                created_at
            FROM data_labeling_embeddings
            ORDER BY created_at DESC
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("\n[INFO] No records found in database")
            return
        
        print(f"\n[OK] Found {len(records)} total records in database\n")
        
        # Count statistics
        with_embeddings = sum(1 for r in records if r[5] == 'YES')
        without_embeddings = len(records) - with_embeddings
        
        print("=" * 60)
        print("Database Statistics")
        print("=" * 60)
        print(f"Total Records: {len(records)}")
        print(f"Records WITH Embeddings: {with_embeddings}")
        print(f"Records WITHOUT Embeddings: {without_embeddings}")
        print(f"Embedding Coverage: {(with_embeddings/len(records)*100):.1f}%")
        
        # Group by modality
        modalities = {}
        for record in records:
            modality = record[3] or 'unknown'
            if modality not in modalities:
                modalities[modality] = {'total': 0, 'with_embedding': 0}
            modalities[modality]['total'] += 1
            if record[5] == 'YES':
                modalities[modality]['with_embedding'] += 1
        
        print("\n" + "=" * 60)
        print("By Modality")
        print("=" * 60)
        for modality, stats in modalities.items():
            coverage = (stats['with_embedding']/stats['total']*100) if stats['total'] > 0 else 0
            print(f"{modality}: {stats['with_embedding']}/{stats['total']} with embeddings ({coverage:.1f}%)")
        
        # Show detailed records
        print("\n" + "=" * 60)
        print("Detailed Records")
        print("=" * 60)
        
        for i, record in enumerate(records, 1):
            file_id, file_name, file_path, modality, category, has_embedding, dims, quality, created = record
            
            # Check if from uploads folder
            is_upload = file_path and 'upload' in file_path.lower() if file_path else False
            
            status_icon = "[HAS]" if has_embedding == 'YES' else "[NO]"
            
            print(f"\n[{i}] {status_icon} {file_name}")
            print(f"    File ID: {file_id}")
            if file_path:
                print(f"    Path: {file_path}")
            print(f"    Modality: {modality or 'N/A'}")
            print(f"    Category: {category or 'N/A'}")
            print(f"    Embedding: {has_embedding}")
            if dims:
                print(f"    Dimensions: {dims}")
            if quality:
                print(f"    Quality Score: {quality:.2f}")
            print(f"    Created: {created}")
            if is_upload:
                print(f"    [UPLOAD_FOLDER]")
        
        # Filter uploads folder records
        upload_records = [r for r in records if r[2] and 'upload' in r[2].lower()]
        
        if upload_records:
            print("\n" + "=" * 60)
            print("Records from UPLOAD_FOLDER")
            print("=" * 60)
            print(f"Total: {len(upload_records)}")
            
            upload_with_embeddings = sum(1 for r in upload_records if r[5] == 'YES')
            upload_without_embeddings = len(upload_records) - upload_with_embeddings
            
            print(f"With Embeddings: {upload_with_embeddings}")
            print(f"Without Embeddings: {upload_without_embeddings}")
            
            print("\nDetails:")
            for record in upload_records:
                file_id, file_name, file_path, modality, category, has_embedding, dims, quality, created = record
                status = "[HAS EMBEDDING]" if has_embedding == 'YES' else "[NO EMBEDDING]"
                print(f"  - {file_name}: {status}")
                if has_embedding == 'YES' and dims:
                    print(f"    Dimensions: {dims}")
        else:
            print("\n[INFO] No records found from UPLOAD_FOLDER")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Database query failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_all_embeddings()


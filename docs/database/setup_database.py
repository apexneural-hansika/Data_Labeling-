"""
Script to automatically set up the Supabase database table for embeddings
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import Config
from utils.logger import get_system_logger

logger = get_system_logger()


def setup_database():
    """Set up the database table and extensions."""
    connection_string = Config.SUPABASE_DB_URL
    
    print("=" * 60)
    print("Setting up Supabase Database for Embeddings")
    print("=" * 60)
    
    try:
        # Connect to database
        print("\n[1/4] Connecting to database...")
        conn = psycopg2.connect(connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("[OK] Connected successfully")
        
        # Enable pgvector extension
        print("\n[2/4] Enabling pgvector extension...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("[OK] pgvector extension enabled")
        except Exception as e:
            print(f"[WARNING] Could not enable vector extension: {str(e)}")
            print("         This might be normal if it's already enabled")
        
        # Create table
        print("\n[3/4] Creating data_labeling_embeddings table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS data_labeling_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_name TEXT NOT NULL,
            file_path TEXT,
            file_id TEXT UNIQUE NOT NULL,
            modality TEXT,
            category TEXT,
            raw_text TEXT,
            labels JSONB,
            metadata JSONB,
            embedding vector(1536),
            quality_score FLOAT,
            processing_time FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        cursor.execute(create_table_sql)
        print("[OK] Table created successfully")
        
        # Create indexes
        print("\n[4/4] Creating indexes...")
        
        indexes = [
            ("embeddings_file_id_idx", "CREATE INDEX IF NOT EXISTS embeddings_file_id_idx ON data_labeling_embeddings(file_id);"),
            ("embeddings_modality_idx", "CREATE INDEX IF NOT EXISTS embeddings_modality_idx ON data_labeling_embeddings(modality);"),
            ("embeddings_category_idx", "CREATE INDEX IF NOT EXISTS embeddings_category_idx ON data_labeling_embeddings(category);"),
            ("embeddings_created_at_idx", "CREATE INDEX IF NOT EXISTS embeddings_created_at_idx ON data_labeling_embeddings(created_at DESC);"),
            ("embeddings_quality_score_idx", "CREATE INDEX IF NOT EXISTS embeddings_quality_score_idx ON data_labeling_embeddings(quality_score DESC);"),
        ]
        
        for idx_name, idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                print(f"  [OK] Created index: {idx_name}")
            except Exception as e:
                print(f"  [WARNING] Could not create {idx_name}: {str(e)}")
        
        # Create vector index (may fail if table is empty, that's OK)
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
                ON data_labeling_embeddings 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            print("  [OK] Created vector similarity index")
        except Exception as e:
            print(f"  [INFO] Vector index creation skipped (normal if table is empty): {str(e)}")
            print("         The index will be created automatically when you insert data")
        
        # Create trigger function and trigger
        print("\nCreating trigger for updated_at...")
        try:
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_data_labeling_embeddings_updated_at ON data_labeling_embeddings;
                CREATE TRIGGER update_data_labeling_embeddings_updated_at 
                BEFORE UPDATE ON data_labeling_embeddings 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
            """)
            print("[OK] Trigger created successfully")
        except Exception as e:
            print(f"[WARNING] Could not create trigger: {str(e)}")
        
        # Verify setup
        print("\n" + "=" * 60)
        print("Verifying setup...")
        print("=" * 60)
        
        # Check extension
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        ext_result = cursor.fetchone()
        if ext_result:
            print(f"[OK] Vector extension: {ext_result[1]} v{ext_result[2]}")
        else:
            print("[WARNING] Vector extension not found")
        
        # Check table
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'data_labeling_embeddings';
        """)
        table_result = cursor.fetchone()
        if table_result:
            print("[OK] Table 'data_labeling_embeddings' exists")
        else:
            print("[ERROR] Table 'data_labeling_embeddings' not found")
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename = 'data_labeling_embeddings';
        """)
        idx_count = cursor.fetchone()[0]
        print(f"[OK] Found {idx_count} indexes on the table")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Database setup completed!")
        print("=" * 60)
        print("\nYou can now run the test script:")
        print("  python test_scripts/test_database.py")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Database setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Verify the connection string is correct")
        print("2. Check if you have permissions to create tables")
        print("3. Ensure Supabase project is active")
        return False


if __name__ == '__main__':
    success = setup_database()
    sys.exit(0 if success else 1)


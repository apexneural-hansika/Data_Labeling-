"""
Database module for storing embeddings in Supabase PostgreSQL with pgvector
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
from psycopg2.pool import SimpleConnectionPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import get_system_logger
from config import Config
from utils.embedding_providers import create_embedding_provider, get_embedding_dimension

logger = get_system_logger()


class EmbeddingDatabase:
    """
    Database handler for storing and retrieving embeddings using Supabase PostgreSQL with pgvector.
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        pool_size: int = 5,
        embedding_provider_type: Optional[str] = None
    ):
        """
        Initialize the embedding database.
        
        Args:
            connection_string: PostgreSQL connection string
            openai_api_key: OpenAI API key for generating embeddings (optional)
            pool_size: Connection pool size
            embedding_provider_type: Type of embedding provider ('auto', 'huggingface', 'openai')
        """
        self.connection_string = connection_string or os.getenv(
            'SUPABASE_DB_URL',
            'postgresql://postgres.saynendmovtnshkdtyei:hansika123@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres'
        )
        
        self.pool_size = pool_size
        
        # Determine embedding provider type
        provider_type = embedding_provider_type or Config.EMBEDDING_PROVIDER
        
        # Get OpenAI key if needed
        if provider_type in ['openai', 'auto']:
            if openai_api_key:
                if openai_api_key.startswith('sk-or-'):
                    self.openai_api_key = Config.get_openai_key_for_embeddings()
                else:
                    self.openai_api_key = openai_api_key
            else:
                self.openai_api_key = Config.get_openai_key_for_embeddings()
        else:
            self.openai_api_key = None
        
        # Initialize embedding provider
        self.embedding_provider = create_embedding_provider(
            provider_type=provider_type,
            api_key=self.openai_api_key,
            model_name=Config.HUGGINGFACE_MODEL
        )
        
        if self.embedding_provider:
            # Get embedding dimension for this provider
            self.embedding_dimension = get_embedding_dimension(
                provider_type=provider_type,
                model_name=Config.HUGGINGFACE_MODEL if provider_type == 'huggingface' else None
            )
            logger.info("Embedding provider initialized", 
                       provider=provider_type,
                       dimension=self.embedding_dimension)
        else:
            self.embedding_dimension = 384  # Default
            logger.warning("No embedding provider available. Embedding generation will not work.")
        
        # Initialize connection pool
        try:
            self.pool = SimpleConnectionPool(
                1, pool_size, self.connection_string
            )
            logger.info("Database connection pool created", pool_size=pool_size)
        except Exception as e:
            logger.error("Failed to create database connection pool", error=str(e))
            self.pool = None
            raise
    
    def _get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise ConnectionError("Database connection pool not initialized")
        return self.pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using the configured provider.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector or None if generation fails
        """
        if not self.embedding_provider:
            logger.warning("Embedding provider not available, cannot generate embedding")
            return None
        
        try:
            embedding = self.embedding_provider.generate_embedding(text)
            if embedding:
                logger.debug("Embedding generated", 
                           text_length=len(text), 
                           embedding_dim=len(embedding),
                           dimension=self.embedding_dimension)
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return None
    
    def store_embedding(
        self,
        file_id: str,
        file_name: str,
        output_data: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> bool:
        """
        Store output data as embedding in the database.
        
        Args:
            file_id: Unique identifier for the file
            file_name: Name of the file
            output_data: The complete output JSON data
            file_path: Path to the original file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.pool:
            logger.error("Database connection pool not available")
            return False
        
        conn = None
        try:
            # Prepare text for embedding
            # Combine relevant fields to create a meaningful text representation
            text_parts = []
            
            # Add raw text if available
            if output_data.get('raw_text'):
                text_parts.append(f"Content: {output_data['raw_text']}")
            
            # Add labels information
            if output_data.get('labels'):
                labels_str = json.dumps(output_data['labels'], indent=2)
                text_parts.append(f"Labels: {labels_str}")
            
            # Add category and modality
            if output_data.get('category'):
                text_parts.append(f"Category: {output_data['category']}")
            if output_data.get('modality'):
                text_parts.append(f"Modality: {output_data['modality']}")
            
            # Add quality information
            if output_data.get('quality_score'):
                text_parts.append(f"Quality Score: {output_data['quality_score']}")
            
            # Combine all parts
            embedding_text = "\n\n".join(text_parts)
            
            if not embedding_text.strip():
                logger.warning("No text available for embedding", file_id=file_id)
                embedding_text = f"File: {file_name}"
            
            # Generate embedding
            embedding = self.generate_embedding(embedding_text)
            
            if not embedding:
                logger.warning("Failed to generate embedding, storing without embedding", file_id=file_id)
            else:
                # Handle dimension mismatch: pad or truncate to match database schema
                # Database table uses 1536 (OpenAI), but HuggingFace uses 384
                target_dim = 1536  # Database schema dimension
                if len(embedding) != target_dim:
                    if len(embedding) < target_dim:
                        # Pad with zeros if smaller (e.g., HuggingFace 384 -> 1536)
                        # Note: Padding with zeros is not ideal for similarity search
                        # but allows storing different dimension embeddings in same table
                        padding = [0.0] * (target_dim - len(embedding))
                        embedding = embedding + padding
                        logger.debug("Padded embedding", 
                                   original_dim=len(embedding) - len(padding), 
                                   padded_dim=len(embedding),
                                   provider_dim=self.embedding_dimension)
                    else:
                        # Truncate if larger (shouldn't happen, but handle it)
                        embedding = embedding[:target_dim]
                        logger.debug("Truncated embedding", 
                                   original_dim=len(embedding), 
                                   truncated_dim=target_dim)
            
            # Get connection from pool
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Prepare data for insertion
            insert_data = {
                'file_id': file_id,
                'file_name': file_name,
                'file_path': file_path,
                'modality': output_data.get('modality'),
                'category': output_data.get('category'),
                'raw_text': output_data.get('raw_text', '')[:10000],  # Limit text length
                'labels': Json(output_data.get('labels', {})),
                'metadata': Json({
                    'quality_score': output_data.get('quality_score'),
                    'quality_status': output_data.get('quality_status'),
                    'processing_time': output_data.get('processing_time'),
                    'timestamp': output_data.get('timestamp'),
                    'agentic_system': output_data.get('agentic_system', False),
                    'agents_involved': output_data.get('agents_involved', []),
                    'extraction_method': output_data.get('extraction_method'),
                    'confidence': output_data.get('confidence'),
                }),
                'embedding': embedding,
                'quality_score': output_data.get('quality_score'),
                'processing_time': output_data.get('processing_time')
            }
            
            # Insert or update record
            query = """
                INSERT INTO data_labeling_embeddings (
                    file_id, file_name, file_path, modality, category,
                    raw_text, labels, metadata, embedding,
                    quality_score, processing_time
                ) VALUES (
                    %(file_id)s, %(file_name)s, %(file_path)s, %(modality)s, %(category)s,
                    %(raw_text)s, %(labels)s, %(metadata)s, %(embedding)s::vector,
                    %(quality_score)s, %(processing_time)s
                )
                ON CONFLICT (file_id) 
                DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    file_path = EXCLUDED.file_path,
                    modality = EXCLUDED.modality,
                    category = EXCLUDED.category,
                    raw_text = EXCLUDED.raw_text,
                    labels = EXCLUDED.labels,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    quality_score = EXCLUDED.quality_score,
                    processing_time = EXCLUDED.processing_time,
                    updated_at = NOW()
            """
            
            cursor.execute(query, insert_data)
            conn.commit()
            
            logger.info("Embedding stored successfully", file_id=file_id, file_name=file_name)
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error("Failed to store embedding", file_id=file_id, error=str(e))
            return False
        finally:
            if conn:
                cursor.close()
                self._return_connection(conn)
    
    def search_similar(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7,
        modality: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            modality: Filter by modality (optional)
            category: Filter by category (optional)
            
        Returns:
            List of similar records with similarity scores
        """
        if not self.pool:
            logger.error("Database connection pool not available")
            return []
        
        # Generate embedding for query
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query with filters
            where_clauses = []
            params = {'query_embedding': query_embedding, 'threshold': threshold, 'limit': limit}
            
            if modality:
                where_clauses.append("modality = %(modality)s")
                params['modality'] = modality
            
            if category:
                where_clauses.append("category = %(category)s")
                params['category'] = category
            
            where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT 
                    id,
                    file_id,
                    file_name,
                    file_path,
                    modality,
                    category,
                    raw_text,
                    labels,
                    metadata,
                    quality_score,
                    processing_time,
                    created_at,
                    1 - (embedding <=> %(query_embedding)s::vector) as similarity
                FROM data_labeling_embeddings
                WHERE embedding IS NOT NULL
                    AND (1 - (embedding <=> %(query_embedding)s::vector)) >= %(threshold)s
                    {where_sql}
                ORDER BY embedding <=> %(query_embedding)s::vector
                LIMIT %(limit)s
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert results to dictionaries
            columns = [desc[0] for desc in cursor.description]
            similar_records = []
            
            for row in results:
                record = dict(zip(columns, row))
                # Convert JSONB fields back to dicts
                if record.get('labels'):
                    record['labels'] = dict(record['labels'])
                if record.get('metadata'):
                    record['metadata'] = dict(record['metadata'])
                similar_records.append(record)
            
            logger.info("Similarity search completed", 
                       query_length=len(query_text),
                       results_count=len(similar_records))
            
            return similar_records
            
        except Exception as e:
            logger.error("Failed to search similar embeddings", error=str(e))
            return []
        finally:
            if conn:
                cursor.close()
                self._return_connection(conn)
    
    def get_by_file_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get embedding record by file_id.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Record dictionary or None if not found
        """
        if not self.pool:
            logger.error("Database connection pool not available")
            return None
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id, file_id, file_name, file_path, modality, category,
                    raw_text, labels, metadata, embedding, quality_score,
                    processing_time, created_at, updated_at
                FROM data_labeling_embeddings
                WHERE file_id = %s
            """
            
            cursor.execute(query, (file_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                record = dict(zip(columns, result))
                # Convert JSONB fields
                if record.get('labels'):
                    record['labels'] = dict(record['labels'])
                if record.get('metadata'):
                    record['metadata'] = dict(record['metadata'])
                return record
            
            return None
            
        except Exception as e:
            logger.error("Failed to get record by file_id", file_id=file_id, error=str(e))
            return None
        finally:
            if conn:
                cursor.close()
                self._return_connection(conn)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.pool:
            return {'error': 'Database connection pool not available'}
        
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(embedding) as records_with_embeddings,
                    AVG(quality_score) as avg_quality_score,
                    COUNT(DISTINCT modality) as unique_modalities,
                    COUNT(DISTINCT category) as unique_categories
                FROM data_labeling_embeddings
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            columns = [desc[0] for desc in cursor.description]
            stats = dict(zip(columns, result))
            
            # Ensure all numeric fields are properly handled
            for key in ['total_records', 'records_with_embeddings', 'unique_modalities', 'unique_categories']:
                if stats.get(key) is None:
                    stats[key] = 0
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return {'error': str(e)}
        finally:
            if conn:
                cursor.close()
                self._return_connection(conn)
    
    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


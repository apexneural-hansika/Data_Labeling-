# Supabase pgvector Setup - Complete Summary

## ✅ What Has Been Set Up

### 1. Database Module (`utils/database.py`)
- Complete `EmbeddingDatabase` class for storing and retrieving embeddings
- Connection pooling for efficient database access
- Automatic embedding generation using OpenAI
- Similarity search using cosine distance
- Statistics and query methods

### 2. Configuration (`config.py`)
- Added `SUPABASE_DB_URL` configuration
- Added `ENABLE_EMBEDDING_STORAGE` flag to enable/disable storage

### 3. Integration (`orchestrator_agentic.py`)
- Automatically stores embeddings after processing files
- Integrated into the existing workflow
- Graceful error handling (won't break if database fails)

### 4. Documentation
- `supabase_setup.md` - Detailed setup guide
- `supabase_migration.sql` - SQL script for database setup
- `EMBEDDING_SETUP.md` - Quick start guide
- `test_scripts/test_database.py` - Test suite

### 5. Dependencies (`requirements_agentic.txt`)
- Added `psycopg2-binary==2.9.9` for PostgreSQL connectivity

## 🚀 Quick Start

### Step 1: Set Up Supabase Database

1. Open Supabase Dashboard → SQL Editor
2. Copy and paste the contents of `supabase_migration.sql`
3. Run the SQL script

This creates:
- `vector` extension
- `data_labeling_embeddings` table
- Indexes for efficient queries
- Triggers for automatic timestamp updates

### Step 2: Install Dependencies

```bash
pip install -r requirements_agentic.txt
```

### Step 3: Configure Environment

Add to `.env` file (or use defaults in config.py):

```env
SUPABASE_DB_URL=postgresql://postgres.saynendmovtnshkdtyei:hansika123@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=your-openai-api-key
ENABLE_EMBEDDING_STORAGE=true
```

### Step 4: Test

```bash
python test_scripts/test_database.py
```

### Step 5: Use It!

The system will automatically store embeddings when you process files. No additional code needed!

## 📊 Database Schema

```sql
data_labeling_embeddings
├── id (UUID, Primary Key)
├── file_id (TEXT, Unique)
├── file_name (TEXT)
├── file_path (TEXT)
├── modality (TEXT) - text_document, image, audio
├── category (TEXT)
├── raw_text (TEXT)
├── labels (JSONB)
├── metadata (JSONB)
├── embedding (vector(1536)) - OpenAI embedding
├── quality_score (FLOAT)
├── processing_time (FLOAT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

## 🔍 Features

### Automatic Storage
- Embeddings are automatically generated and stored when files are processed
- Combines content, labels, and metadata into a single embedding
- Uses OpenAI's `text-embedding-ada-002` model (1536 dimensions)

### Similarity Search
- Search for similar outputs using natural language queries
- Filter by modality, category, quality score
- Results ranked by cosine similarity

### Statistics
- Track total records, average quality scores
- Count unique modalities and categories
- Monitor embedding coverage

## 📝 Example Usage

### Search Similar Outputs

```python
from utils.database import EmbeddingDatabase
from config import Config

db = EmbeddingDatabase(
    connection_string=Config.SUPABASE_DB_URL,
    openai_api_key=Config.OPENAI_API_KEY
)

# Find similar financial documents
results = db.search_similar(
    query_text="financial statements and audit reports",
    limit=10,
    threshold=0.7,
    modality="text_document"
)

for result in results:
    print(f"{result['file_name']}: {result['similarity']:.3f}")
```

### Get Record by File ID

```python
record = db.get_by_file_id("your-file-id")
if record:
    print(f"Quality: {record['quality_score']}")
    print(f"Labels: {record['labels']}")
```

## ⚙️ Configuration Options

### Enable/Disable Storage
```env
ENABLE_EMBEDDING_STORAGE=false  # Disable embedding storage
```

### Connection Pooling
The database uses connection pooling (default: 5 connections). Adjust in code if needed.

### Embedding Model
Currently uses `text-embedding-ada-002`. To change, modify `utils/database.py`.

## 🔒 Security Notes

1. **Never commit connection strings** - Already in `.gitignore`
2. **Use environment variables** - Store in `.env` file
3. **Connection pooling** - Reduces connection overhead
4. **Row Level Security** - Can be enabled in Supabase for multi-user scenarios

## 🐛 Troubleshooting

### "Extension vector does not exist"
- Run `CREATE EXTENSION vector;` in Supabase SQL Editor

### "Table does not exist"
- Run `supabase_migration.sql` in Supabase SQL Editor

### "Connection refused"
- Check connection string
- Verify Supabase project is active
- Check network connectivity

### "Failed to generate embedding"
- Verify OpenAI API key is set
- Check API quota/limits
- Ensure text content is not empty

## 📚 Files Created/Modified

### New Files
- `utils/database.py` - Database module
- `supabase_setup.md` - Detailed setup guide
- `supabase_migration.sql` - SQL migration script
- `EMBEDDING_SETUP.md` - Quick start guide
- `test_scripts/test_database.py` - Test suite
- `SETUP_SUMMARY.md` - This file

### Modified Files
- `config.py` - Added database configuration
- `orchestrator_agentic.py` - Integrated embedding storage
- `requirements_agentic.txt` - Added psycopg2-binary

## 🎯 Next Steps

1. Run the SQL migration in Supabase
2. Install dependencies: `pip install -r requirements_agentic.txt`
3. Test the setup: `python test_scripts/test_database.py`
4. Start processing files - embeddings will be stored automatically!

## 📖 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

---

**Your connection string is already configured in `config.py` as the default.**
**Just run the SQL migration and you're ready to go!** 🚀


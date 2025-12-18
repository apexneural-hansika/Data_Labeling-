# Supabase pgvector Setup Guide

This guide will help you set up Supabase with pgvector extension to store embeddings for your data labeling outputs.

## Step 1: Enable pgvector Extension in Supabase

1. **Go to your Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run the following SQL to enable pgvector:**
   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

4. **Verify the extension is installed:**
   ```sql
   -- Check if vector extension is enabled
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

## Step 2: Create the Embeddings Table

Run the following SQL in the Supabase SQL Editor to create the table for storing embeddings:

```sql
-- Create embeddings table
CREATE TABLE IF NOT EXISTS data_labeling_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_id TEXT UNIQUE NOT NULL,  -- Unique identifier for the file
    modality TEXT,  -- text_document, image, audio
    category TEXT,
    raw_text TEXT,  -- Store the original text content
    labels JSONB,  -- Store the labels as JSON
    metadata JSONB,  -- Store additional metadata
    embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
    quality_score FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
ON data_labeling_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS embeddings_file_id_idx ON data_labeling_embeddings(file_id);
CREATE INDEX IF NOT EXISTS embeddings_modality_idx ON data_labeling_embeddings(modality);
CREATE INDEX IF NOT EXISTS embeddings_category_idx ON data_labeling_embeddings(category);
CREATE INDEX IF NOT EXISTS embeddings_created_at_idx ON data_labeling_embeddings(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_data_labeling_embeddings_updated_at 
BEFORE UPDATE ON data_labeling_embeddings 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();
```

## Step 3: Set Up Connection String

Your connection string is already provided:
```
postgresql://postgres.saynendmovtnshkdtyei:hansika123@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres
```

**Important Security Note:** 
- Store this connection string in your `.env` file, not in code
- Never commit connection strings to version control
- Consider using Supabase's connection pooling for better performance

## Step 4: Test the Connection

You can test the connection using the Python script provided in `test_scripts/test_database.py`:

```bash
python test_scripts/test_database.py
```

## Step 5: Verify Setup

Run this query in Supabase SQL Editor to verify everything is set up correctly:

```sql
-- Check table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'data_labeling_embeddings';

-- Check vector extension
SELECT extname, extversion 
FROM pg_extension 
WHERE extname = 'vector';

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'data_labeling_embeddings';
```

## Additional Configuration

### Connection Pooling (Recommended for Production)

Supabase provides connection pooling. You can use:
- **Session mode**: `postgresql://...@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres`
- **Transaction mode**: `postgresql://...@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres`

### Row Level Security (Optional)

If you want to add security, you can enable Row Level Security:

```sql
-- Enable RLS (optional)
ALTER TABLE data_labeling_embeddings ENABLE ROW LEVEL SECURITY;

-- Create policy (adjust based on your needs)
CREATE POLICY "Allow all operations for authenticated users" 
ON data_labeling_embeddings 
FOR ALL 
USING (true);
```

## Troubleshooting

### Issue: Extension not found
**Solution**: Make sure you're running the SQL as a superuser. In Supabase, this should work by default.

### Issue: Vector dimension mismatch
**Solution**: OpenAI embeddings are 1536 dimensions. If using a different model, adjust the vector size in the table definition.

### Issue: Connection timeout
**Solution**: 
- Check your network connection
- Verify the connection string is correct
- Try using the direct connection (non-pooler) if pooler is having issues

### Issue: Index creation fails
**Solution**: The ivfflat index requires at least some data. If the table is empty, the index creation might fail. You can create it after inserting some data.

## Next Steps

After completing this setup:
1. Add the connection string to your `.env` file
2. Install required Python packages (see requirements_agentic.txt)
3. The system will automatically store embeddings when processing files


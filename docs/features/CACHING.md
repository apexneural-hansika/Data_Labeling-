# Caching System Documentation

## Overview

The caching system prevents reprocessing of files that have already been processed, significantly improving performance and reducing API costs.

## Features

### 1. In-Memory Cache ✅
- Fast LRU (Least Recently Used) cache
- Configurable size and TTL
- Thread-safe operations
- Automatic eviction of oldest entries

### 2. Database Cache ✅
- Uses embedding database for persistent cache
- Retrieves previously processed results
- Works across application restarts

### 3. File Hash-Based Deduplication ✅
- Computes SHA256 hash of file content
- Identifies duplicate files even with different names
- Prevents reprocessing identical content

### 4. Cache Statistics ✅
- Track cache hits/misses
- Monitor cache size and performance
- Debug cache behavior

## How It Works

### Processing Flow

```
1. File Upload
   ↓
2. Compute File Hash
   ↓
3. Check In-Memory Cache
   ├─→ Cache Hit → Return Cached Result (FAST!)
   └─→ Cache Miss
       ↓
4. Check Database Cache
   ├─→ Cache Hit → Return Cached Result + Store in Memory
   └─→ Cache Miss
       ↓
5. Process File (Full Pipeline)
   ↓
6. Store Result in Cache
   ↓
7. Return Result
```

### Cache Key Generation

The system uses two types of cache keys:

1. **File Hash**: `file_hash:{sha256_hash}`
   - Based on file content
   - Identifies duplicate files

2. **File ID**: `file_id:{file_id}`
   - Based on file identifier
   - Faster lookup when file_id is known

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Enable/Disable Caching
ENABLE_CACHING=true
ENABLE_MEMORY_CACHE=true
ENABLE_DB_CACHE=true

# Memory Cache Settings
MEMORY_CACHE_SIZE=100          # Maximum cached items
MEMORY_CACHE_TTL=3600          # Time-to-live in seconds (1 hour)
```

### Configuration Options

| Option | Default | Description |
|-------|---------|-------------|
| `ENABLE_CACHING` | `true` | Enable/disable caching system |
| `ENABLE_MEMORY_CACHE` | `true` | Enable in-memory cache |
| `ENABLE_DB_CACHE` | `true` | Enable database cache lookup |
| `MEMORY_CACHE_SIZE` | `100` | Maximum items in memory cache |
| `MEMORY_CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |

## Usage

### Automatic Caching

Caching is **automatic** when enabled. No code changes needed!

```python
from orchestrator_agentic import AgenticOrchestrator

orchestrator = AgenticOrchestrator(...)

# First call - processes file
result1 = orchestrator.process_file('file.pdf')

# Second call - returns cached result (FAST!)
result2 = orchestrator.process_file('file.pdf')
# result2['cache_hit'] = True
```

### Cache Hit Detection

Results include cache metadata:

```json
{
  "file_name": "test.pdf",
  "modality": "text_document",
  "category": "document_processing",
  "quality_score": 0.85,
  "cache_hit": true,
  "cache_source": "memory",
  "cached": true,
  "cached_at": "2025-11-21T15:30:00"
}
```

### Manual Cache Operations

```python
from utils.cache import ResultCache

# Initialize cache
cache = ResultCache(
    embedding_db=embedding_db,
    enable_memory_cache=True,
    enable_db_cache=True
)

# Get cached result
cached = cache.get_cached_result('file.pdf')

# Store result
cache.store_result('file.pdf', result)

# Clear cache
cache.clear_cache()

# Get statistics
stats = cache.get_cache_stats()
```

## Performance Benefits

### Speed Improvement

- **Cache Hit**: ~1-10ms (vs 5-30 seconds for processing)
- **Speedup**: 1000-3000x faster for cached results

### Cost Savings

- **API Calls**: Eliminated for cached files
- **Processing Time**: Near-zero for cached results
- **Database Queries**: Reduced load

### Example

Processing a 1MB PDF:
- **First time**: 15 seconds, $0.01 API cost
- **Cached**: 0.01 seconds, $0.00 API cost
- **Savings**: 1500x faster, 100% cost reduction

## Cache Behavior

### Cache Hit Scenarios

1. **Same File, Same Content**
   - File hash matches
   - Returns cached result immediately

2. **Same File, Different Name**
   - Content hash matches
   - Returns cached result (deduplication)

3. **Recently Processed**
   - In memory cache
   - Fastest retrieval

### Cache Miss Scenarios

1. **New File**
   - Never processed before
   - Full processing pipeline

2. **Modified File**
   - Content hash changed
   - Treated as new file

3. **Expired Cache**
   - TTL exceeded
   - Reprocesses file

## Cache Invalidation

### Automatic Invalidation

- **TTL Expiration**: Entries expire after TTL
- **LRU Eviction**: Oldest entries evicted when cache is full
- **File Modification**: Different hash = cache miss

### Manual Invalidation

```python
# Clear all caches
orchestrator.result_cache.clear_cache()

# Clear specific entry (by removing from cache)
# This happens automatically on file modification
```

## Monitoring

### Cache Statistics

```python
stats = orchestrator.result_cache.get_cache_stats()

# Returns:
{
  'memory_cache_enabled': True,
  'db_cache_enabled': True,
  'memory_cache': {
    'size': 45,
    'max_size': 100,
    'ttl_seconds': 3600,
    'keys': ['file_hash:abc123...', ...]
  }
}
```

### Logging

Cache operations are logged:

```
INFO - Cache hit (memory) | file_path=test.pdf
INFO - Cache miss - Processing file | file_path=new.pdf
INFO - Result stored in cache | file_path=test.pdf
```

## Best Practices

### 1. Enable Both Caches
- Memory cache for speed
- Database cache for persistence

### 2. Set Appropriate TTL
- Short TTL (1 hour) for frequently changing files
- Long TTL (24 hours) for stable content

### 3. Monitor Cache Size
- Adjust `MEMORY_CACHE_SIZE` based on memory available
- Larger cache = more hits but more memory

### 4. Use File Hashes
- Automatic deduplication
- Prevents reprocessing identical content

## Troubleshooting

### Cache Not Working

1. **Check Configuration**
   ```python
   # Verify caching is enabled
   print(Config.ENABLE_CACHING)  # Should be True
   ```

2. **Check Logs**
   - Look for "Cache hit" or "Cache miss" messages
   - Verify cache initialization

3. **Verify File Hash**
   - Same file should produce same hash
   - Different files = different hashes

### Cache Always Misses

- **File Modified**: Check if file content changed
- **Cache Cleared**: Verify cache wasn't cleared
- **TTL Expired**: Check cache TTL settings

### Performance Issues

- **Cache Too Small**: Increase `MEMORY_CACHE_SIZE`
- **Too Many Evictions**: Increase cache size or TTL
- **Database Slow**: Check database connection

## Advanced Usage

### Custom Cache Key

```python
# Use file_id for faster lookup
cache.get_cached_result('file.pdf', file_id='unique_id_123')
```

### Cache Warming

```python
# Pre-populate cache with common files
for file_path in common_files:
    if not cache.get_cached_result(file_path):
        result = process_file(file_path)
        cache.store_result(file_path, result)
```

### Cache Analytics

```python
# Track cache performance
cache_hits = 0
cache_misses = 0

for file in files:
    cached = cache.get_cached_result(file)
    if cached:
        cache_hits += 1
    else:
        cache_misses += 1

hit_rate = cache_hits / (cache_hits + cache_misses)
print(f"Cache hit rate: {hit_rate:.2%}")
```

## Summary

The caching system provides:
- ✅ **1000x+ speed improvement** for cached results
- ✅ **100% cost savings** on API calls for cached files
- ✅ **Automatic deduplication** via file hashing
- ✅ **Persistent caching** via database
- ✅ **Configurable TTL** and cache size
- ✅ **Thread-safe** operations
- ✅ **Zero code changes** needed (automatic)

Caching is enabled by default and works automatically!


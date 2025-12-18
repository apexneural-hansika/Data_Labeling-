"""
Test script for caching system
"""
import os
import sys
import time
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache import FileCache, ResultCache
from config import Config
from utils.logger import get_system_logger

logger = get_system_logger()


def test_file_cache():
    """Test in-memory file cache."""
    print("=" * 60)
    print("Testing In-Memory File Cache")
    print("=" * 60)
    
    cache = FileCache(max_size=5, ttl_seconds=60)
    
    # Test storing and retrieving
    test_result = {
        'file_name': 'test.pdf',
        'modality': 'text_document',
        'category': 'test',
        'quality_score': 0.85
    }
    
    cache.set('test_key_1', test_result)
    retrieved = cache.get('test_key_1')
    
    assert retrieved is not None, "Should retrieve cached result"
    assert retrieved['file_name'] == 'test.pdf', "Retrieved result should match"
    print("[OK] Cache store and retrieve working")
    
    # Test cache miss
    assert cache.get('non_existent_key') is None, "Should return None for non-existent key"
    print("[OK] Cache miss handling working")
    
    # Test LRU eviction
    for i in range(6):
        cache.set(f'key_{i}', {'data': i})
    
    # First key should be evicted (oldest)
    assert cache.get('key_0') is None, "Oldest key should be evicted"
    assert cache.get('key_5') is not None, "Newest key should exist"
    print("[OK] LRU eviction working")
    
    # Test stats
    stats = cache.get_stats()
    assert stats['size'] == 5, "Cache size should be 5"
    print("[OK] Cache stats working")
    
    print("[SUCCESS] In-memory cache tests passed\n")
    return True


def test_result_cache():
    """Test result cache with file hash."""
    print("=" * 60)
    print("Testing Result Cache")
    print("=" * 60)
    
    # Create a temporary test file
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    test_file.write("This is a test file for caching")
    test_file.close()
    
    try:
        # Initialize cache without database (memory only)
        cache = ResultCache(
            embedding_db=None,
            enable_memory_cache=True,
            enable_db_cache=False
        )
        
        # Test file hash computation
        cache_key = cache._get_cache_key(test_file.name)
        assert cache_key.startswith('file_hash:'), "Cache key should start with file_hash:"
        print("[OK] File hash computation working")
        
        # Test storing and retrieving
        test_result = {
            'file_name': os.path.basename(test_file.name),
            'modality': 'text_document',
            'category': 'test',
            'quality_score': 0.85,
            'success': True
        }
        
        cache.store_result(test_file.name, test_result)
        retrieved = cache.get_cached_result(test_file.name)
        
        assert retrieved is not None, "Should retrieve cached result"
        assert retrieved['file_name'] == os.path.basename(test_file.name), "Retrieved result should match"
        # Note: 'cached' key is only added when retrieving from database cache
        print("[OK] Result cache store and retrieve working")
        
        # Test cache hit
        cached = cache.get_cached_result(test_file.name)
        assert cached is not None, "Should get cached result on second call"
        print("[OK] Cache hit working")
        
        # Test cache stats
        stats = cache.get_cache_stats()
        assert stats['memory_cache_enabled'] == True, "Memory cache should be enabled"
        print("[OK] Cache stats working")
        
        print("[SUCCESS] Result cache tests passed\n")
        return True
        
    finally:
        # Clean up
        try:
            os.unlink(test_file.name)
        except:
            pass


def test_cache_expiration():
    """Test cache expiration."""
    print("=" * 60)
    print("Testing Cache Expiration")
    print("=" * 60)
    
    # Create cache with very short TTL
    cache = FileCache(max_size=10, ttl_seconds=1)  # 1 second TTL
    
    test_result = {'data': 'test'}
    cache.set('expire_key', test_result)
    
    # Should be available immediately
    assert cache.get('expire_key') is not None, "Should retrieve before expiration"
    print("[OK] Cache entry available before expiration")
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired now
    assert cache.get('expire_key') is None, "Should return None after expiration"
    print("[OK] Cache expiration working")
    
    print("[SUCCESS] Cache expiration tests passed\n")
    return True


def test_cache_integration():
    """Test cache integration with file processing simulation."""
    print("=" * 60)
    print("Testing Cache Integration")
    print("=" * 60)
    
    # Create a test file
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    test_file.write("Test content for caching integration")
    test_file.close()
    
    try:
        cache = ResultCache(
            embedding_db=None,
            enable_memory_cache=True,
            enable_db_cache=False
        )
        
        # Simulate first processing (cache miss)
        cached_result = cache.get_cached_result(test_file.name)
        assert cached_result is None, "First call should be cache miss"
        print("[OK] First call: cache miss")
        
        # Simulate processing result
        result = {
            'file_name': os.path.basename(test_file.name),
            'modality': 'text_document',
            'category': 'test',
            'quality_score': 0.9,
            'success': True,
            'processing_time': 2.5
        }
        
        # Store result
        cache.store_result(test_file.name, result)
        
        # Simulate second processing (cache hit)
        cached_result = cache.get_cached_result(test_file.name)
        assert cached_result is not None, "Second call should be cache hit"
        assert cached_result['quality_score'] == 0.9, "Cached result should match"
        print("[OK] Second call: cache hit")
        
        # Test with different file (should be cache miss)
        test_file2 = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        test_file2.write("Different content")
        test_file2.close()
        
        try:
            cached_result2 = cache.get_cached_result(test_file2.name)
            assert cached_result2 is None, "Different file should be cache miss"
            print("[OK] Different file: cache miss")
        finally:
            os.unlink(test_file2.name)
        
        print("[SUCCESS] Cache integration tests passed\n")
        return True
        
    finally:
        # Clean up
        try:
            os.unlink(test_file.name)
        except:
            pass


if __name__ == '__main__':
    print("\n")
    print("Caching System Test Suite")
    print("=" * 60)
    print("\nTesting caching functionality...\n")
    
    results = []
    
    try:
        results.append(("File Cache", test_file_cache()))
    except Exception as e:
        print(f"[ERROR] File cache test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("File Cache", False))
    
    try:
        results.append(("Result Cache", test_result_cache()))
    except Exception as e:
        print(f"[ERROR] Result cache test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("Result Cache", False))
    
    try:
        results.append(("Cache Expiration", test_cache_expiration()))
    except Exception as e:
        print(f"[ERROR] Cache expiration test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("Cache Expiration", False))
    
    try:
        results.append(("Cache Integration", test_cache_integration()))
    except Exception as e:
        print(f"[ERROR] Cache integration test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("Cache Integration", False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All caching tests passed!")
    else:
        print("[INFO] Some tests failed - check errors above")
    print("=" * 60)


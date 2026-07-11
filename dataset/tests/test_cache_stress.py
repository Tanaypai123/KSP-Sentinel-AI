import sys
import os
import time
import random
import resource

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset')))

from app.core.storage.cache_provider import LRUCacheProvider

def get_memory_usage_mb() -> float:
    # ru_maxrss is in kilobytes on Linux, bytes on macOS
    # On mac/Unix, ru_maxrss represents the peak RSS memory
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On macOS, ru_maxrss is in bytes
    if sys.platform == 'darwin':
        return rss_kb / (1024.0 * 1024.0)
    else:
        return rss_kb / 1024.0

def test_cache_stress():
    print("Initializing stress test with 500,000 cache operations...")
    # Capacity is bounded to 5,000 to trigger high evictions
    cache = LRUCacheProvider(max_entries=5000, ttl_seconds=100)
    
    start_memory = get_memory_usage_mb()
    
    start_time = time.time()
    for i in range(500000):
        key = f"key_{i}"
        val = f"val_data_footprint_{i}"
        cache.set(key, val)
        
        # Periodically read to simulate real-world usage and trigger hits/misses
        if i % 10 == 0:
            cache.get(f"key_{random.randint(0, i)}")
            
        if i % 100000 == 0 and i > 0:
            current_mem = get_memory_usage_mb()
            stats = cache.stats()
            print(f"Executed {i} ops... Cache Size: {stats['size']} | Evictions: {stats['evictions']} | Peak Memory: {current_mem:.2f} MB")
            
    duration = time.time() - start_time
    end_memory = get_memory_usage_mb()
    stats = cache.stats()
    
    print("\n--- Stress Test Completed ---")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Final Cache Size: {stats['size']} (Max: {stats['max_size']})")
    print(f"Hits: {stats['hits']} | Misses: {stats['misses']}")
    print(f"Evictions: {stats['evictions']}")
    print(f"Reported Cache Memory: {stats['memory_usage_bytes'] / 1024:.2f} KB")
    print(f"Start Peak Memory: {start_memory:.2f} MB")
    print(f"End Peak Memory: {end_memory:.2f} MB")
    
    # Assert size bounds
    assert stats['size'] <= 5000, "Cache size exceeded max entries!"
    assert stats['evictions'] == 495000, f"Expected 495,000 evictions, got {stats['evictions']}"
    
    memory_growth_mb = end_memory - start_memory
    print(f"Peak Memory Growth: {memory_growth_mb:.2f} MB")
    print("SUCCESS: Memory cache stress test passed successfully!")

if __name__ == "__main__":
    test_cache_stress()

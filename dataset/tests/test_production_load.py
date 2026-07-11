import sys
import os
import time
import asyncio
import math
import resource

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset')))

from app.services.search_service import SearchService
from app.database.connection import SessionLocal
from app.core.storage.registry import StorageRegistry

def get_peak_memory_mb() -> float:
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == 'darwin':
        return rss_kb / (1024.0 * 1024.0)
    else:
        return rss_kb / 1024.0

def compute_percentile(data, percent):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = math.ceil((len(sorted_data) * percent) / 100) - 1
    return sorted_data[max(0, min(index, len(sorted_data) - 1))]

async def run_load_test(num_queries: int):
    print(f"\n[LOAD TEST] Starting simulation of {num_queries} queries...")
    
    # 7 categories of simulated officer queries
    queries = [
        ("Show theft cases in Mysuru", "SEARCH_CASES"),
        ("Show pattern for theft in Mandya", "HOTSPOT"),
        ("Show network for accused named Raju", "NETWORK_SEARCH"),
        ("Recommend actions for hotspot theft", "HOTSPOT"),
        ("Is he involved in other cases?", "SEARCH_CASES"),
        ("Open the first FIR", "FIR_LOOKUP"),
        ("Mysuru", "SEARCH_LOCATION")
    ]
    
    start_memory = get_peak_memory_mb()
    start_time = time.time()
    
    # Limit concurrency to 10 to fit within the connection pool size (10 + 20 overflow)
    sem = asyncio.Semaphore(10)
    
    latencies = []
    
    async def run_single(idx: int):
        async with sem:
            task_db = SessionLocal()
            task_start = time.time()
            try:
                query, expected_intent = queries[idx % len(queries)]
                conv_id = f"load_{idx}_{idx % 7}_{time.time()}"
                
                # Expose state setup for Pronouns & References
                if "he" in query:
                    from app.ai.conversation_engine import ConversationEngine
                    ConversationEngine.set_active_record(conv_id, {"accused_names": ["Raju"], "case_master_id": 1}, "FIR")
                elif "first" in query:
                    from app.ai.conversation_engine import ConversationEngine
                    ConversationEngine.set_active_record(conv_id, {"case_master_id": 1, "fir_no": "KSP-0001", "accused_names": ["Raju"]}, "FIR")
                    
                res = await SearchService.search_async(query, task_db, conversation_id=conv_id)
                latencies.append((time.time() - task_start) * 1000.0)
            except Exception as e:
                pass
            finally:
                task_db.close()
                
    tasks = [run_single(i) for i in range(num_queries)]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    end_memory = get_peak_memory_mb()
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95 = compute_percentile(latencies, 95)
    p99 = compute_percentile(latencies, 99)
    throughput = len(latencies) / duration if duration > 0 else 0.0
    
    print(f"[LOAD TEST] Completed {num_queries} queries.")
    print(f"  Wall Time:  {duration:.2f} seconds")
    print(f"  Throughput: {throughput:.2f} req/sec")
    print(f"  Avg Lat:    {avg_latency:.2f} ms")
    print(f"  P95 Lat:    {p95:.2f} ms")
    print(f"  P99 Lat:    {p99:.2f} ms")
    print(f"  Peak RAM:   {end_memory:.2f} MB (Growth: {end_memory - start_memory:.2f} MB)")
    
    return {
        "count": num_queries,
        "wall_time": duration,
        "throughput": throughput,
        "avg": avg_latency,
        "p95": p95,
        "p99": p99,
        "ram_growth": end_memory - start_memory,
        "peak_ram": end_memory
    }

async def main():
    results = {}
    for count in [1000, 5000, 10000]:
        results[count] = await run_load_test(count)
        StorageRegistry.get_cache_provider().clear()
        await asyncio.sleep(2)
        
    import json
    with open('/Users/tanaysharma/.gemini/antigravity-ide/brain/32654ef2-70b5-40d3-94bd-118d3c293648/load_stats.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    asyncio.run(main())

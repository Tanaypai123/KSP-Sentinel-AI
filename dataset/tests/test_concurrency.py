import threading
import uuid
import random
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset')))

from app.services.search_service import SearchService
from app.ai.conversation_engine import ConversationEngine
from app.database.connection import get_db

def run_session(session_id: str, query_sequence: list):
    # Provision a unique DB session for thread safety
    db = next(get_db())
    try:
        for query, expected_intent in query_sequence:
            res = SearchService.search(query, db, conversation_id=session_id)
            # Verify the loaded conversation ID matches the request
            state = ConversationEngine.get_state(session_id)
            if state.conversation_id != session_id:
                raise AssertionError(f"Context leak detected! Expected {session_id}, found state for {state.conversation_id}")
            
            # Verify state content is completely isolated
            if "Mysuru" in query and state.last_entities.get("district") != "Mysuru":
                raise AssertionError(f"Entity leak detected! Session {session_id} had district {state.last_entities.get('district')}")
            if "Dharwad" in query and state.last_entities.get("district") != "Dharwad":
                raise AssertionError(f"Entity leak detected! Session {session_id} had district {state.last_entities.get('district')}")
                
            time.sleep(random.uniform(0.001, 0.005))
    finally:
        db.close()

def test_concurrency(num_sessions: int):
    print(f"Simulating {num_sessions} parallel conversations...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(num_sessions):
            session_id = f"session_{i}_{uuid.uuid4()}"
            district = "Mysuru" if i % 2 == 0 else "Dharwad"
            query_seq = [
                (f"Show theft cases in {district}", "SEARCH_CASES"),
            ]
            futures.append(executor.submit(run_session, session_id, query_seq))
            
        # Verify all threads complete without assertion errors
        for f in futures:
            f.result()
            
    print(f"✅ Simulation of {num_sessions} parallel conversations completed successfully with 0% context bleed.")

if __name__ == "__main__":
    start = time.time()
    test_concurrency(100)
    test_concurrency(500)
    test_concurrency(1000)
    duration = time.time() - start
    print(f"\nAll concurrency tests passed! Total time: {duration:.2f} seconds.")

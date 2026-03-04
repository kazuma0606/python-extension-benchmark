"""Pure Python implementation of parallel computation functions."""

import threading
from typing import List


def parallel_compute(data: List[float], num_threads: int) -> float:
    """Perform parallel computation (sum) using multiple threads.
    
    Args:
        data: Data to process
        num_threads: Number of threads to use
        
    Returns:
        Sum of all elements in data
    """
    if not data:
        return 0.0
    
    if num_threads <= 0:
        raise ValueError("num_threads must be positive")
    
    # For single thread, just compute directly
    if num_threads == 1:
        return sum(data)
    
    # Split data into chunks for each thread
    chunk_size = len(data) // num_threads
    remainder = len(data) % num_threads
    
    results = [0.0] * num_threads
    threads = []
    
    def compute_chunk(thread_id: int, start: int, end: int):
        """Compute sum for a chunk of data."""
        results[thread_id] = sum(data[start:end])
    
    # Create and start threads
    start_idx = 0
    for i in range(num_threads):
        # Distribute remainder across first threads
        end_idx = start_idx + chunk_size + (1 if i < remainder else 0)
        
        if start_idx < len(data):
            thread = threading.Thread(
                target=compute_chunk,
                args=(i, start_idx, end_idx)
            )
            threads.append(thread)
            thread.start()
        
        start_idx = end_idx
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Return total sum
    return sum(results)

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <thread>
#include <future>
#include <algorithm>
#include <numeric>

namespace py = pybind11;

/**
 * Compute sum of a chunk of data
 */
double compute_chunk(const std::vector<double>& data, size_t start, size_t end) {
    double sum = 0.0;
    for (size_t i = start; i < end; ++i) {
        sum += data[i];
    }
    return sum;
}

/**
 * Perform parallel computation (sum) using multiple threads with std::thread
 */
double parallel_compute(const std::vector<double>& data, int num_threads) {
    if (data.empty()) {
        return 0.0;
    }
    
    if (num_threads <= 0) {
        throw std::invalid_argument("num_threads must be positive");
    }
    
    // For single thread, compute directly
    if (num_threads == 1) {
        return std::accumulate(data.begin(), data.end(), 0.0);
    }
    
    size_t data_size = data.size();
    
    // Limit threads to data size
    if (static_cast<size_t>(num_threads) > data_size) {
        num_threads = static_cast<int>(data_size);
    }
    
    // Calculate chunk sizes
    size_t chunk_size = data_size / num_threads;
    size_t remainder = data_size % num_threads;
    
    // Create futures for async computation
    std::vector<std::future<double>> futures;
    futures.reserve(num_threads);
    
    // Launch threads
    size_t start_idx = 0;
    for (int i = 0; i < num_threads; ++i) {
        // Distribute remainder across first threads
        size_t current_chunk_size = chunk_size + (static_cast<size_t>(i) < remainder ? 1 : 0);
        size_t end_idx = start_idx + current_chunk_size;
        
        if (start_idx < data_size) {
            // Use std::async with std::launch::async to ensure actual threading
            futures.push_back(
                std::async(std::launch::async, compute_chunk, 
                          std::cref(data), start_idx, end_idx)
            );
        }
        
        start_idx = end_idx;
    }
    
    // Collect results
    double total_sum = 0.0;
    for (auto& future : futures) {
        total_sum += future.get();
    }
    
    return total_sum;
}

PYBIND11_MODULE(parallel, m) {
    m.doc() = "C++ implementation of parallel computation functions";
    
    m.def("parallel_compute", &parallel_compute, 
          "Perform parallel computation (sum) using multiple threads with std::thread",
          py::arg("data"), py::arg("num_threads"));
}
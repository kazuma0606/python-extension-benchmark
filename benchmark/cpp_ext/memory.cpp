#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <algorithm>

namespace py = pybind11;

/**
 * Sort an array of integers using std::sort
 */
std::vector<int> sort_array(const std::vector<int>& arr) {
    if (arr.empty()) {
        return std::vector<int>();
    }
    
    // Create a copy to sort
    std::vector<int> result = arr;
    
    // Sort using std::sort (typically introsort - hybrid of quicksort, heapsort, and insertion sort)
    std::sort(result.begin(), result.end());
    
    return result;
}

/**
 * Filter array elements >= threshold
 */
std::vector<int> filter_array(const std::vector<int>& arr, int threshold) {
    std::vector<int> result;
    
    // Reserve space to avoid multiple reallocations
    // This is an optimization - we don't know exact size but this helps
    result.reserve(arr.size());
    
    // Filter elements
    for (int value : arr) {
        if (value >= threshold) {
            result.push_back(value);
        }
    }
    
    // Shrink to fit actual size
    result.shrink_to_fit();
    
    return result;
}

PYBIND11_MODULE(memory, m) {
    m.doc() = "C++ implementation of memory operation functions";
    
    m.def("sort_array", &sort_array, 
          "Sort an array of integers using std::sort",
          py::arg("arr"));
    
    m.def("filter_array", &filter_array, 
          "Filter array elements >= threshold",
          py::arg("arr"), py::arg("threshold"));
}
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

/**
 * Find all prime numbers up to n using Sieve of Eratosthenes
 */
std::vector<int> find_primes(int n) {
    if (n < 2) {
        return std::vector<int>();
    }
    
    // Initialize sieve: true means potentially prime
    std::vector<bool> is_prime(n + 1, true);
    is_prime[0] = is_prime[1] = false;
    
    // Sieve of Eratosthenes
    int sqrt_n = static_cast<int>(std::sqrt(n));
    for (int i = 2; i <= sqrt_n; ++i) {
        if (is_prime[i]) {
            // Mark all multiples of i as not prime
            for (int j = i * i; j <= n; j += i) {
                is_prime[j] = false;
            }
        }
    }
    
    // Collect primes
    std::vector<int> primes;
    for (int i = 2; i <= n; ++i) {
        if (is_prime[i]) {
            primes.push_back(i);
        }
    }
    
    return primes;
}

/**
 * Multiply two matrices
 */
std::vector<std::vector<double>> matrix_multiply(
    const std::vector<std::vector<double>>& a,
    const std::vector<std::vector<double>>& b) {
    
    if (a.empty() || b.empty()) {
        return std::vector<std::vector<double>>(1, std::vector<double>());
    }
    
    size_t m = a.size();
    size_t n = a[0].size();
    size_t n_b = b.size();
    size_t p = b[0].size();
    
    // Verify dimensions are compatible
    if (n_b != n) {
        throw std::invalid_argument("Incompatible matrix dimensions");
    }
    
    // Verify all rows have consistent dimensions
    for (const auto& row : a) {
        if (row.size() != n) {
            throw std::invalid_argument("Inconsistent matrix dimensions in matrix a");
        }
    }
    
    for (const auto& row : b) {
        if (row.size() != p) {
            throw std::invalid_argument("Inconsistent matrix dimensions in matrix b");
        }
    }
    
    // Initialize result matrix with zeros
    std::vector<std::vector<double>> result(m, std::vector<double>(p, 0.0));
    
    // Perform matrix multiplication
    for (size_t i = 0; i < m; ++i) {
        for (size_t j = 0; j < p; ++j) {
            for (size_t k = 0; k < n; ++k) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    return result;
}

PYBIND11_MODULE(numeric, m) {
    m.doc() = "C++ implementation of numeric computation functions";
    
    m.def("find_primes", &find_primes, 
          "Find all prime numbers up to n using Sieve of Eratosthenes",
          py::arg("n"));
    
    m.def("matrix_multiply", &matrix_multiply, 
          "Multiply two matrices",
          py::arg("a"), py::arg("b"));
}
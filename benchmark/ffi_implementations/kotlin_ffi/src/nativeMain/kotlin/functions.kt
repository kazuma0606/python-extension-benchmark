/**
 * Kotlin/Native FFI Implementation for Python Benchmark System
 * 
 * This file contains Kotlin/Native implementations of benchmark functions
 * with C ABI compatibility for FFI integration with Python.
 */

import kotlinx.cinterop.*
import kotlin.math.sqrt
import kotlin.native.concurrent.ThreadLocal

/**
 * Find all prime numbers up to n using Sieve of Eratosthenes
 * Returns allocated array that must be freed by caller
 */
@CName("find_primes_ffi")
fun findPrimesFFI(n: Int, count: CPointer<IntVar>): CPointer<IntVar>? {
    if (n < 2) {
        count.pointed.value = 0
        return null
    }
    
    // Create sieve array
    val sieve = BooleanArray(n + 1) { true }
    sieve[0] = false
    sieve[1] = false
    
    // Sieve of Eratosthenes algorithm
    val limit = sqrt(n.toDouble()).toInt()
    for (i in 2..limit) {
        if (sieve[i]) {
            var j = i * i
            while (j <= n) {
                sieve[j] = false
                j += i
            }
        }
    }
    
    // Count primes first
    var primeCount = 0
    for (i in 2..n) {
        if (sieve[i]) {
            primeCount++
        }
    }
    
    if (primeCount == 0) {
        count.pointed.value = 0
        return null
    }
    
    // Allocate result array
    val result = nativeHeap.allocArray<IntVar>(primeCount)
    
    // Collect primes
    var index = 0
    for (i in 2..n) {
        if (sieve[i]) {
            result[index] = i
            index++
        }
    }
    
    count.pointed.value = primeCount
    return result
}

/**
 * Matrix multiplication using efficient Kotlin algorithms
 * Returns allocated result matrix that must be freed by caller
 */
@CName("matrix_multiply_ffi")
fun matrixMultiplyFFI(
    a: CPointer<DoubleVar>, rowsA: Int, colsA: Int,
    b: CPointer<DoubleVar>, rowsB: Int, colsB: Int,
    resultRows: CPointer<IntVar>, resultCols: CPointer<IntVar>
): CPointer<DoubleVar>? {
    // Check dimensions
    if (colsA != rowsB) {
        resultRows.pointed.value = 0
        resultCols.pointed.value = 0
        return null
    }
    
    resultRows.pointed.value = rowsA
    resultCols.pointed.value = colsB
    
    // Allocate result matrix
    val resultSize = rowsA * colsB
    val result = nativeHeap.allocArray<DoubleVar>(resultSize)
    
    // Initialize result matrix to zero
    for (i in 0 until resultSize) {
        result[i] = 0.0
    }
    
    // Perform matrix multiplication with cache-friendly access pattern
    for (i in 0 until rowsA) {
        for (k in 0 until colsA) {
            val aik = a[i * colsA + k]
            for (j in 0 until colsB) {
                result[i * colsB + j] += aik * b[k * colsB + j]
            }
        }
    }
    
    return result
}

/**
 * Sort array using Kotlin's optimized sorting algorithms
 * Returns allocated sorted array that must be freed by caller
 */
@CName("sort_array_ffi")
fun sortArrayFFI(arr: CPointer<IntVar>, size: Int): CPointer<IntVar>? {
    if (size <= 0) return null
    
    // Convert to Kotlin array for efficient sorting
    val kotlinArray = IntArray(size) { arr[it] }
    
    // Use Kotlin's optimized sort (introsort implementation)
    kotlinArray.sort()
    
    // Allocate result array
    val result = nativeHeap.allocArray<IntVar>(size)
    
    // Copy sorted data to result
    for (i in 0 until size) {
        result[i] = kotlinArray[i]
    }
    
    return result
}

/**
 * Filter array elements using functional programming approach
 * Returns allocated filtered array that must be freed by caller
 */
@CName("filter_array_ffi")
fun filterArrayFFI(
    arr: CPointer<IntVar>, size: Int, threshold: Int,
    resultSize: CPointer<IntVar>
): CPointer<IntVar>? {
    if (size == 0) {
        resultSize.pointed.value = 0
        return null
    }
    
    // First pass: count matching elements
    var count = 0
    for (i in 0 until size) {
        if (arr[i] >= threshold) {
            count++
        }
    }
    
    if (count == 0) {
        resultSize.pointed.value = 0
        return null
    }
    
    // Allocate result array
    val result = nativeHeap.allocArray<IntVar>(count)
    
    // Second pass: collect matching elements
    var index = 0
    for (i in 0 until size) {
        val value = arr[i]
        if (value >= threshold) {
            result[index] = value
            index++
        }
    }
    
    resultSize.pointed.value = count
    return result
}

/**
 * Parallel computation using divide-and-conquer approach
 * Efficient concurrent processing for sum calculation
 */
@CName("parallel_compute_ffi")
fun parallelComputeFFI(data: CPointer<DoubleVar>, size: Int, numThreads: Int): Double {
    if (size == 0) return 0.0
    if (size == 1) return data[0]
    
    // Convert to Kotlin array for easier processing
    val kotlinArray = DoubleArray(size) { data[it] }
    
    // For small arrays or single thread, use sequential computation
    if (size < 1000 || numThreads <= 1) {
        return kotlinArray.sum()
    }
    
    // Use divide-and-conquer approach for parallel-like processing
    return parallelSumRecursive(kotlinArray, 0, size, 1000)
}

/**
 * Free memory allocated by Kotlin FFI functions
 */
@CName("free_memory_ffi")
fun freeMemoryFFI(ptr: COpaquePointer?) {
    if (ptr != null) {
        nativeHeap.free(ptr)
    }
}

/**
 * Alternative parallel compute using divide-and-conquer approach
 * More suitable for Kotlin/Native's execution model
 */
private fun parallelSumRecursive(arr: DoubleArray, start: Int, end: Int, threshold: Int = 1000): Double {
    val length = end - start
    
    if (length <= threshold) {
        // Sequential sum for small chunks
        var sum = 0.0
        for (i in start until end) {
            sum += arr[i]
        }
        return sum
    }
    
    // Divide and conquer
    val mid = start + length / 2
    val leftSum = parallelSumRecursive(arr, start, mid, threshold)
    val rightSum = parallelSumRecursive(arr, mid, end, threshold)
    
    return leftSum + rightSum
}

/**
 * Utility function to validate matrix dimensions
 */
private fun isValidMatrixDimensions(rowsA: Int, colsA: Int, rowsB: Int, colsB: Int): Boolean {
    return rowsA > 0 && colsA > 0 && rowsB > 0 && colsB > 0 && colsA == rowsB
}

/**
 * Utility function for efficient prime checking
 */
private fun isPrime(n: Int): Boolean {
    if (n < 2) return false
    if (n == 2) return true
    if (n % 2 == 0) return false
    
    val limit = sqrt(n.toDouble()).toInt()
    for (i in 3..limit step 2) {
        if (n % i == 0) return false
    }
    return true
}
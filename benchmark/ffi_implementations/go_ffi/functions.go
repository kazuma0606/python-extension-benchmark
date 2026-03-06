package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"math"
	"runtime"
	"sort"
	"sync"
	"unsafe"
)

//export find_primes_ffi
func find_primes_ffi(n C.int, count *C.int) *C.int {
	limit := int(n)
	if limit < 2 {
		*count = 0
		return nil
	}

	// Sieve of Eratosthenes
	sieve := make([]bool, limit+1)
	for i := 2; i <= limit; i++ {
		sieve[i] = true
	}

	for i := 2; i*i <= limit; i++ {
		if sieve[i] {
			for j := i * i; j <= limit; j += i {
				sieve[j] = false
			}
		}
	}

	// Collect primes
	primes := make([]int, 0, limit/int(math.Log(float64(limit))))
	for i := 2; i <= limit; i++ {
		if sieve[i] {
			primes = append(primes, i)
		}
	}

	// Allocate C array and copy results
	*count = C.int(len(primes))
	if len(primes) == 0 {
		return nil
	}

	// Allocate memory for result array
	result := (*C.int)(C.malloc(C.size_t(len(primes)) * C.size_t(unsafe.Sizeof(C.int(0)))))
	resultSlice := (*[1 << 30]C.int)(unsafe.Pointer(result))[:len(primes):len(primes)]
	
	for i, prime := range primes {
		resultSlice[i] = C.int(prime)
	}

	return result
}

//export matrix_multiply_ffi
func matrix_multiply_ffi(a *C.double, rows_a, cols_a C.int, b *C.double, rows_b, cols_b C.int, result_rows, result_cols *C.int) *C.double {
	ra, ca := int(rows_a), int(cols_a)
	rb, cb := int(rows_b), int(cols_b)

	// Check matrix dimensions
	if ca != rb {
		*result_rows = 0
		*result_cols = 0
		return nil
	}

	*result_rows = C.int(ra)
	*result_cols = C.int(cb)

	// Convert C arrays to Go slices
	aSlice := (*[1 << 30]C.double)(unsafe.Pointer(a))[:ra*ca:ra*ca]
	bSlice := (*[1 << 30]C.double)(unsafe.Pointer(b))[:rb*cb:rb*cb]

	// Allocate result array
	resultSize := ra * cb
	result := (*C.double)(C.malloc(C.size_t(resultSize) * C.size_t(unsafe.Sizeof(C.double(0)))))
	resultSlice := (*[1 << 30]C.double)(unsafe.Pointer(result))[:resultSize:resultSize]

	// Parallel matrix multiplication using goroutines
	numWorkers := runtime.NumCPU()
	if ra < numWorkers {
		numWorkers = ra
	}

	var wg sync.WaitGroup
	rowsPerWorker := ra / numWorkers

	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func(worker int) {
			defer wg.Done()
			
			startRow := worker * rowsPerWorker
			endRow := startRow + rowsPerWorker
			if worker == numWorkers-1 {
				endRow = ra // Last worker handles remaining rows
			}

			for i := startRow; i < endRow; i++ {
				for j := 0; j < cb; j++ {
					sum := 0.0
					for k := 0; k < ca; k++ {
						sum += float64(aSlice[i*ca+k]) * float64(bSlice[k*cb+j])
					}
					resultSlice[i*cb+j] = C.double(sum)
				}
			}
		}(w)
	}

	wg.Wait()
	return result
}

//export sort_array_ffi
func sort_array_ffi(arr *C.int, size C.int) *C.int {
	n := int(size)
	if n <= 0 {
		return nil
	}

	// Convert C array to Go slice
	inputSlice := (*[1 << 30]C.int)(unsafe.Pointer(arr))[:n:n]
	
	// Convert to int slice for sorting
	goSlice := make([]int, n)
	for i := 0; i < n; i++ {
		goSlice[i] = int(inputSlice[i])
	}

	// Sort using Go's standard library
	sort.Ints(goSlice)

	// Allocate result array
	result := (*C.int)(C.malloc(C.size_t(n) * C.size_t(unsafe.Sizeof(C.int(0)))))
	resultSlice := (*[1 << 30]C.int)(unsafe.Pointer(result))[:n:n]

	// Copy sorted data to result
	for i := 0; i < n; i++ {
		resultSlice[i] = C.int(goSlice[i])
	}

	return result
}

//export filter_array_ffi
func filter_array_ffi(arr *C.int, size C.int, threshold C.int, result_size *C.int) *C.int {
	n := int(size)
	thresh := int(threshold)

	if n == 0 {
		*result_size = 0
		return nil
	}

	// Convert C array to Go slice
	inputSlice := (*[1 << 30]C.int)(unsafe.Pointer(arr))[:n:n]
	
	// Filter elements
	filtered := make([]int, 0, n)
	for i := 0; i < n; i++ {
		if int(inputSlice[i]) >= thresh {
			filtered = append(filtered, int(inputSlice[i]))
		}
	}

	*result_size = C.int(len(filtered))
	if len(filtered) == 0 {
		return nil
	}

	// Allocate result array
	result := (*C.int)(C.malloc(C.size_t(len(filtered)) * C.size_t(unsafe.Sizeof(C.int(0)))))
	resultSlice := (*[1 << 30]C.int)(unsafe.Pointer(result))[:len(filtered):len(filtered)]

	for i, val := range filtered {
		resultSlice[i] = C.int(val)
	}

	return result
}

//export parallel_compute_ffi
func parallel_compute_ffi(data *C.double, size C.int, num_threads C.int) C.double {
	n := int(size)
	threads := int(num_threads)

	if n == 0 {
		return 0.0
	}

	// Convert C array to Go slice
	dataSlice := (*[1 << 30]C.double)(unsafe.Pointer(data))[:n:n]

	// Use specified number of goroutines or CPU count
	if threads <= 0 {
		threads = runtime.NumCPU()
	}
	if threads > n {
		threads = n
	}

	// Channel for partial sums
	results := make(chan float64, threads)
	elementsPerThread := n / threads

	var wg sync.WaitGroup

	for i := 0; i < threads; i++ {
		wg.Add(1)
		go func(threadID int) {
			defer wg.Done()
			
			start := threadID * elementsPerThread
			end := start + elementsPerThread
			if threadID == threads-1 {
				end = n // Last thread handles remaining elements
			}

			sum := 0.0
			for j := start; j < end; j++ {
				sum += float64(dataSlice[j])
			}
			
			results <- sum
		}(i)
	}

	// Close results channel when all goroutines finish
	go func() {
		wg.Wait()
		close(results)
	}()

	// Sum all partial results
	totalSum := 0.0
	for partialSum := range results {
		totalSum += partialSum
	}

	return C.double(totalSum)
}

//export free_memory_ffi
func free_memory_ffi(ptr unsafe.Pointer) {
	if ptr != nil {
		C.free(ptr)
	}
}

func main() {} // Required for cgo
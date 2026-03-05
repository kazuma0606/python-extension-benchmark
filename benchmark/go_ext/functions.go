package main

import "C"
import (
	"math"
	"runtime"
	"sort"
	"sync"
	"unsafe"
)

//export find_primes
func find_primes(n C.int, result *C.int, count *C.int) {
	limit := int(n)
	if limit < 2 {
		*count = 0
		return
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

	// Copy to C array
	*count = C.int(len(primes))
	resultSlice := (*[1 << 30]C.int)(unsafe.Pointer(result))[:len(primes):len(primes)]
	for i, prime := range primes {
		resultSlice[i] = C.int(prime)
	}
}

//export matrix_multiply
func matrix_multiply(a *C.double, rows_a, cols_a C.int, b *C.double, rows_b, cols_b C.int, result *C.double) {
	ra, ca := int(rows_a), int(cols_a)
	rb, cb := int(rows_b), int(cols_b)

	// Convert C arrays to Go slices
	aSlice := (*[1 << 30]C.double)(unsafe.Pointer(a))[:ra*ca:ra*ca]
	bSlice := (*[1 << 30]C.double)(unsafe.Pointer(b))[:rb*cb:rb*cb]
	resultSlice := (*[1 << 30]C.double)(unsafe.Pointer(result))[:ra*cb:ra*cb]

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
}

//export sort_array
func sort_array(arr *C.int, length C.int) {
	n := int(length)
	if n <= 1 {
		return
	}

	// Convert C array to Go slice
	slice := (*[1 << 30]C.int)(unsafe.Pointer(arr))[:n:n]
	
	// Convert to int slice for sorting
	goSlice := make([]int, n)
	for i := 0; i < n; i++ {
		goSlice[i] = int(slice[i])
	}

	// Sort using Go's standard library
	sort.Ints(goSlice)

	// Copy back to C array
	for i := 0; i < n; i++ {
		slice[i] = C.int(goSlice[i])
	}
}

//export filter_array
func filter_array(arr *C.int, length C.int, threshold C.int, result *C.int, count *C.int) {
	n := int(length)
	thresh := int(threshold)

	if n == 0 {
		*count = 0
		return
	}

	// Convert C arrays to Go slices
	inputSlice := (*[1 << 30]C.int)(unsafe.Pointer(arr))[:n:n]
	
	// Filter elements
	filtered := make([]int, 0, n)
	for i := 0; i < n; i++ {
		if int(inputSlice[i]) >= thresh {
			filtered = append(filtered, int(inputSlice[i]))
		}
	}

	// Copy to result array
	*count = C.int(len(filtered))
	if len(filtered) > 0 {
		resultSlice := (*[1 << 30]C.int)(unsafe.Pointer(result))[:len(filtered):len(filtered)]
		for i, val := range filtered {
			resultSlice[i] = C.int(val)
		}
	}
}

//export parallel_compute
func parallel_compute(data *C.double, length C.int, num_threads C.int) C.double {
	n := int(length)
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

func main() {} // Required for cgo
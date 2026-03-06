! Fortran FFI implementation using iso_c_binding for C ABI compatibility
! This module provides C-compatible functions for FFI integration

module fortran_ffi_functions
    use iso_c_binding
    implicit none

    ! C standard library interfaces for memory management
    interface
        function c_malloc(size) bind(c, name="malloc") result(ptr)
            use iso_c_binding
            type(c_ptr) :: ptr
            integer(c_size_t), value :: size
        end function c_malloc

        subroutine c_free(ptr) bind(c, name="free")
            use iso_c_binding
            type(c_ptr), value :: ptr
        end subroutine c_free
    end interface

contains

    ! Find all prime numbers up to n using Sieve of Eratosthenes
    ! C signature: int* find_primes_ffi(int n, int* count)
    function find_primes_ffi(n, count) result(primes_ptr) bind(c, name='find_primes_ffi')
        integer(c_int), intent(in), value :: n
        integer(c_int), intent(out) :: count
        type(c_ptr) :: primes_ptr

        logical, allocatable :: is_prime(:)
        integer(c_int), pointer :: primes(:)
        integer :: i, j, sqrt_n, prime_count

        ! Initialize
        allocate(is_prime(0:n))
        is_prime = .true.
        if (n >= 0) is_prime(0) = .false.
        if (n >= 1) is_prime(1) = .false.

        ! Sieve of Eratosthenes
        sqrt_n = int(sqrt(real(n))) + 1
        do i = 2, min(sqrt_n, n)
            if (is_prime(i)) then
                do j = i*i, n, i
                    is_prime(j) = .false.
                end do
            end if
        end do

        ! Count primes
        prime_count = 0
        do i = 2, n
            if (is_prime(i)) then
                prime_count = prime_count + 1
            end if
        end do

        count = 0
        if (prime_count == 0) then
            deallocate(is_prime)
            primes_ptr = c_null_ptr
            return
        end if

        ! Allocate result using C malloc so caller can free it
        primes_ptr = c_malloc(int(prime_count, c_size_t) * c_sizeof(1_c_int))
        call c_f_pointer(primes_ptr, primes, [prime_count])

        ! Collect primes
        count = 0
        do i = 2, n
            if (is_prime(i)) then
                count = count + 1
                primes(count) = i
            end if
        end do

        deallocate(is_prime)
    end function find_primes_ffi

    ! Matrix multiplication: C = A * B
    ! C signature: double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
    !                                         double* b, int rows_b, int cols_b,
    !                                         int* result_rows, int* result_cols)
    function matrix_multiply_ffi(a_ptr, rows_a, cols_a, b_ptr, rows_b, cols_b, &
                                result_rows, result_cols) result(c_ptr_result) bind(c, name='matrix_multiply_ffi')
        type(c_ptr), intent(in), value :: a_ptr, b_ptr
        integer(c_int), intent(in), value :: rows_a, cols_a, rows_b, cols_b
        integer(c_int), intent(out) :: result_rows, result_cols
        type(c_ptr) :: c_ptr_result

        real(c_double), pointer :: a(:), b(:), c(:)
        integer :: i, j, k, idx_a, idx_b, idx_c

        ! Check dimensions
        if (cols_a /= rows_b) then
            result_rows = 0
            result_cols = 0
            c_ptr_result = c_null_ptr
            return
        end if

        ! Convert C pointers to Fortran arrays (flattened, row-major)
        call c_f_pointer(a_ptr, a, [rows_a * cols_a])
        call c_f_pointer(b_ptr, b, [rows_b * cols_b])

        ! Set result dimensions
        result_rows = rows_a
        result_cols = cols_b

        ! Allocate result matrix using C malloc
        c_ptr_result = c_malloc(int(result_rows * result_cols, c_size_t) * c_sizeof(1.0_c_double))
        call c_f_pointer(c_ptr_result, c, [result_rows * result_cols])
        c = 0.0_c_double

        ! Perform matrix multiplication (row-major order)
        do i = 1, rows_a
            do j = 1, cols_b
                do k = 1, cols_a
                    idx_a = (i-1) * cols_a + k
                    idx_b = (k-1) * cols_b + j
                    idx_c = (i-1) * result_cols + j
                    c(idx_c) = c(idx_c) + a(idx_a) * b(idx_b)
                end do
            end do
        end do
    end function matrix_multiply_ffi

    ! Sort an array of integers using quicksort
    ! C signature: int* sort_array_ffi(int* arr, int size)
    function sort_array_ffi(arr_ptr, size) result(result_ptr) bind(c, name='sort_array_ffi')
        type(c_ptr), intent(in), value :: arr_ptr
        integer(c_int), intent(in), value :: size
        type(c_ptr) :: result_ptr

        integer(c_int), pointer :: arr(:), result(:)

        ! Convert C pointer to Fortran array
        call c_f_pointer(arr_ptr, arr, [size])

        ! Allocate result array using C malloc and copy input
        result_ptr = c_malloc(int(size, c_size_t) * c_sizeof(1_c_int))
        call c_f_pointer(result_ptr, result, [size])
        result = arr

        ! Sort the array using heapsort (O(n log n) worst case)
        call heapsort(result, size)
    end function sort_array_ffi

    ! Filter array elements >= threshold
    ! C signature: int* filter_array_ffi(int* arr, int size, int threshold, int* result_size)
    function filter_array_ffi(arr_ptr, size, threshold, result_size) result(result_ptr) bind(c, name='filter_array_ffi')
        type(c_ptr), intent(in), value :: arr_ptr
        integer(c_int), intent(in), value :: size, threshold
        integer(c_int), intent(out) :: result_size
        type(c_ptr) :: result_ptr

        integer(c_int), pointer :: arr(:), result(:)
        integer :: i, count

        ! Convert C pointer to Fortran array
        call c_f_pointer(arr_ptr, arr, [size])

        ! Count elements >= threshold
        count = 0
        do i = 1, size
            if (arr(i) >= threshold) then
                count = count + 1
            end if
        end do

        result_size = count

        if (count == 0) then
            result_ptr = c_null_ptr
            return
        end if

        ! Allocate result array using C malloc
        result_ptr = c_malloc(int(count, c_size_t) * c_sizeof(1_c_int))
        call c_f_pointer(result_ptr, result, [count])

        ! Fill result array
        count = 0
        do i = 1, size
            if (arr(i) >= threshold) then
                count = count + 1
                result(count) = arr(i)
            end if
        end do
    end function filter_array_ffi

    ! Perform parallel computation (serial version for compatibility)
    ! C signature: double parallel_compute_ffi(double* data, int size, int num_threads)
    function parallel_compute_ffi(data_ptr, size, num_threads) result(sum_result) bind(c, name='parallel_compute_ffi')
        type(c_ptr), intent(in), value :: data_ptr
        integer(c_int), intent(in), value :: size, num_threads
        real(c_double) :: sum_result

        real(c_double), pointer :: data(:)
        integer :: i

        ! Convert C pointer to Fortran array
        call c_f_pointer(data_ptr, data, [size])

        sum_result = 0.0_c_double
        do i = 1, size
            sum_result = sum_result + data(i)
        end do

    end function parallel_compute_ffi

    ! Free memory allocated by Fortran FFI functions (C malloc)
    ! C signature: void free_memory_ffi(void* ptr)
    subroutine free_memory_ffi(ptr) bind(c, name='free_memory_ffi')
        type(c_ptr), intent(in), value :: ptr
        call c_free(ptr)
    end subroutine free_memory_ffi

    ! Helper subroutines

    ! Heapsort implementation (O(n log n) worst case, no stack overflow risk)
    subroutine heapsort(arr, n)
        integer(c_int), dimension(:), intent(inout) :: arr
        integer, intent(in) :: n
        integer :: i
        integer(c_int) :: temp

        ! Build max heap
        do i = n/2, 1, -1
            call heapify(arr, n, i)
        end do

        ! Extract elements from heap one by one
        do i = n, 2, -1
            temp = arr(1)
            arr(1) = arr(i)
            arr(i) = temp
            call heapify(arr, i-1, 1)
        end do
    end subroutine heapsort

    ! Heapify subtree rooted at index i (iterative to avoid deep recursion)
    subroutine heapify(arr, n, root)
        integer(c_int), dimension(:), intent(inout) :: arr
        integer, intent(in) :: n, root
        integer :: i, largest, left, right
        integer(c_int) :: temp

        i = root
        do while (.true.)
            largest = i
            left = 2 * i
            right = 2 * i + 1

            if (left <= n .and. arr(left) > arr(largest)) largest = left
            if (right <= n .and. arr(right) > arr(largest)) largest = right

            if (largest == i) exit

            temp = arr(i)
            arr(i) = arr(largest)
            arr(largest) = temp
            i = largest
        end do
    end subroutine heapify

end module fortran_ffi_functions

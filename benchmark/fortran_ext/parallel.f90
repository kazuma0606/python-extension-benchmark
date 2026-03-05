! Fortran implementation of parallel computation functions
! Using OpenMP for parallel processing

module parallel_functions
    use omp_lib
    implicit none
    
contains

    ! Perform parallel computation (sum) using multiple threads
    subroutine parallel_compute_impl(data, n, num_threads, result)
        implicit none
        integer, intent(in) :: n, num_threads
        real(8), dimension(n), intent(in) :: data
        real(8), intent(out) :: result
        
        integer :: i
        real(8) :: partial_sum
        
        ! Set number of threads
        call omp_set_num_threads(num_threads)
        
        result = 0.0d0
        
        ! Parallel sum using OpenMP reduction
        !$omp parallel do reduction(+:result) private(i)
        do i = 1, n
            result = result + data(i)
        end do
        !$omp end parallel do
        
    end subroutine parallel_compute_impl
    
    ! Alternative implementation with explicit thread management
    subroutine parallel_compute_explicit(data, n, num_threads, result)
        implicit none
        integer, intent(in) :: n, num_threads
        real(8), dimension(n), intent(in) :: data
        real(8), intent(out) :: result
        
        integer :: i, thread_id, num_threads_used
        integer :: chunk_size, start_idx, end_idx
        real(8) :: local_sum
        
        call omp_set_num_threads(num_threads)
        result = 0.0d0
        
        !$omp parallel private(thread_id, chunk_size, start_idx, end_idx, local_sum, i)
        thread_id = omp_get_thread_num()
        num_threads_used = omp_get_num_threads()
        
        ! Calculate chunk size for this thread
        chunk_size = n / num_threads_used
        start_idx = thread_id * chunk_size + 1
        
        if (thread_id == num_threads_used - 1) then
            end_idx = n  ! Last thread handles remaining elements
        else
            end_idx = start_idx + chunk_size - 1
        end if
        
        ! Compute local sum
        local_sum = 0.0d0
        do i = start_idx, end_idx
            local_sum = local_sum + data(i)
        end do
        
        ! Add to global result (critical section)
        !$omp critical
        result = result + local_sum
        !$omp end critical
        
        !$omp end parallel
        
    end subroutine parallel_compute_explicit

end module parallel_functions
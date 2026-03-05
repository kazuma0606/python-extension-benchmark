! Fortran implementation of numeric computation functions
! Using modern Fortran 90/95 features for better performance

module numeric_functions
    implicit none
    
contains

    ! Find all prime numbers up to n using Sieve of Eratosthenes
    subroutine find_primes_impl(n, primes, count)
        implicit none
        integer, intent(in) :: n
        integer, intent(out) :: count
        integer, dimension(n), intent(out) :: primes
        
        logical, dimension(0:n) :: is_prime
        integer :: i, j, sqrt_n
        
        ! Initialize all numbers as potentially prime
        is_prime = .true.
        is_prime(0) = .false.
        is_prime(1) = .false.
        
        ! Sieve of Eratosthenes
        sqrt_n = int(sqrt(real(n))) + 1
        do i = 2, sqrt_n
            if (is_prime(i)) then
                ! Mark all multiples of i as not prime
                do j = i*i, n, i
                    is_prime(j) = .false.
                end do
            end if
        end do
        
        ! Collect all primes
        count = 0
        do i = 2, n
            if (is_prime(i)) then
                count = count + 1
                primes(count) = i
            end if
        end do
    end subroutine find_primes_impl

    ! Matrix multiplication: C = A * B
    subroutine matrix_multiply_impl(a, b, c, m, n, p)
        implicit none
        integer, intent(in) :: m, n, p
        real(8), dimension(m, n), intent(in) :: a
        real(8), dimension(n, p), intent(in) :: b
        real(8), dimension(m, p), intent(out) :: c
        
        integer :: i, j, k
        real(8) :: temp
        
        ! Initialize result matrix
        c = 0.0d0
        
        ! Perform matrix multiplication with loop optimization
        do j = 1, p
            do k = 1, n
                do i = 1, m
                    c(i, j) = c(i, j) + a(i, k) * b(k, j)
                end do
            end do
        end do
    end subroutine matrix_multiply_impl

end module numeric_functions
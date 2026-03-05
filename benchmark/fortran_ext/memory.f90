! Fortran implementation of memory operation functions
! Using modern Fortran features for array operations

module memory_functions
    implicit none
    
contains

    ! Sort an array of integers using quicksort
    subroutine sort_array_impl(arr, n)
        implicit none
        integer, intent(in) :: n
        integer, dimension(n), intent(inout) :: arr
        
        call quicksort(arr, 1, n)
    end subroutine sort_array_impl
    
    ! Quicksort implementation
    recursive subroutine quicksort(arr, low, high)
        implicit none
        integer, dimension(:), intent(inout) :: arr
        integer, intent(in) :: low, high
        integer :: pivot_index
        
        if (low < high) then
            call partition(arr, low, high, pivot_index)
            call quicksort(arr, low, pivot_index - 1)
            call quicksort(arr, pivot_index + 1, high)
        end if
    end subroutine quicksort
    
    ! Partition function for quicksort
    subroutine partition(arr, low, high, pivot_index)
        implicit none
        integer, dimension(:), intent(inout) :: arr
        integer, intent(in) :: low, high
        integer, intent(out) :: pivot_index
        integer :: pivot, i, j, temp
        
        pivot = arr(high)
        i = low - 1
        
        do j = low, high - 1
            if (arr(j) <= pivot) then
                i = i + 1
                ! Swap arr(i) and arr(j)
                temp = arr(i)
                arr(i) = arr(j)
                arr(j) = temp
            end if
        end do
        
        ! Swap arr(i+1) and arr(high)
        temp = arr(i + 1)
        arr(i + 1) = arr(high)
        arr(high) = temp
        
        pivot_index = i + 1
    end subroutine partition

    ! Filter array elements >= threshold
    subroutine filter_array_impl(arr, n, threshold, result, result_count)
        implicit none
        integer, intent(in) :: n, threshold
        integer, dimension(n), intent(in) :: arr
        integer, dimension(n), intent(out) :: result
        integer, intent(out) :: result_count
        
        integer :: i
        
        result_count = 0
        do i = 1, n
            if (arr(i) >= threshold) then
                result_count = result_count + 1
                result(result_count) = arr(i)
            end if
        end do
    end subroutine filter_array_impl

end module memory_functions
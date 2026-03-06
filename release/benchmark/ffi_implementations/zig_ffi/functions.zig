const std = @import("std");
const math = std.math;
const ArrayList = std.ArrayList;
const Allocator = std.mem.Allocator;
const Thread = std.Thread;

// Global allocator for C interface
var gpa = std.heap.GeneralPurposeAllocator(.{}){};
const allocator = gpa.allocator();

// Export functions for FFI C ABI compatibility
export fn find_primes_ffi(n: c_int, count: *c_int) ?[*]c_int {
    const limit = @as(usize, @intCast(n));
    if (limit < 2) {
        count.* = 0;
        return null;
    }

    // Sieve of Eratosthenes with memory-safe implementation
    var sieve = allocator.alloc(bool, limit + 1) catch {
        count.* = 0;
        return null;
    };
    defer allocator.free(sieve);

    // Initialize sieve
    for (sieve, 0..) |*is_prime, i| {
        is_prime.* = i >= 2;
    }

    // Sieve algorithm
    var i: usize = 2;
    while (i * i <= limit) : (i += 1) {
        if (sieve[i]) {
            var j = i * i;
            while (j <= limit) : (j += i) {
                sieve[j] = false;
            }
        }
    }

    // Count primes first
    var prime_count: usize = 0;
    for (sieve) |is_prime| {
        if (is_prime) {
            prime_count += 1;
        }
    }

    if (prime_count == 0) {
        count.* = 0;
        return null;
    }

    // Allocate result array
    const result = allocator.alloc(c_int, prime_count) catch {
        count.* = 0;
        return null;
    };

    // Collect primes
    var idx: usize = 0;
    for (sieve, 0..) |is_prime, num| {
        if (is_prime) {
            result[idx] = @as(c_int, @intCast(num));
            idx += 1;
        }
    }

    count.* = @as(c_int, @intCast(prime_count));
    return result.ptr;
}

export fn matrix_multiply_ffi(
    a: [*]const f64, rows_a: c_int, cols_a: c_int,
    b: [*]const f64, rows_b: c_int, cols_b: c_int,
    result_rows: *c_int, result_cols: *c_int
) ?[*]f64 {
    const ra = @as(usize, @intCast(rows_a));
    const ca = @as(usize, @intCast(cols_a));
    const rb = @as(usize, @intCast(rows_b));
    const cb = @as(usize, @intCast(cols_b));

    // Check dimensions compatibility
    if (ca != rb) {
        result_rows.* = 0;
        result_cols.* = 0;
        return null;
    }

    result_rows.* = rows_a;
    result_cols.* = cols_b;

    // Allocate result matrix
    const result_size = ra * cb;
    const result = allocator.alloc(f64, result_size) catch {
        result_rows.* = 0;
        result_cols.* = 0;
        return null;
    };

    // Efficient matrix multiplication with cache-friendly access pattern
    for (0..ra) |i| {
        for (0..cb) |j| {
            var sum: f64 = 0.0;
            for (0..ca) |k| {
                sum += a[i * ca + k] * b[k * cb + j];
            }
            result[i * cb + j] = sum;
        }
    }

    return result.ptr;
}

export fn sort_array_ffi(arr: [*]const c_int, size: c_int) ?[*]c_int {
    const n = @as(usize, @intCast(size));
    if (n == 0) return null;

    // Allocate result array
    const result = allocator.alloc(c_int, n) catch return null;

    // Copy input to result
    for (0..n) |i| {
        result[i] = arr[i];
    }

    // Use Zig's standard library sort (introsort - hybrid of quicksort, heapsort, and insertion sort)
    std.sort.heap(c_int, result, {}, comptime std.sort.asc(c_int));

    return result.ptr;
}

export fn filter_array_ffi(arr: [*]const c_int, size: c_int, threshold: c_int, result_size: *c_int) ?[*]c_int {
    const n = @as(usize, @intCast(size));
    const thresh = threshold;

    if (n == 0) {
        result_size.* = 0;
        return null;
    }

    // First pass: count matching elements
    var count: usize = 0;
    for (0..n) |i| {
        if (arr[i] >= thresh) {
            count += 1;
        }
    }

    if (count == 0) {
        result_size.* = 0;
        return null;
    }

    // Allocate result array
    const result = allocator.alloc(c_int, count) catch {
        result_size.* = 0;
        return null;
    };

    // Second pass: collect matching elements
    var idx: usize = 0;
    for (0..n) |i| {
        if (arr[i] >= thresh) {
            result[idx] = arr[i];
            idx += 1;
        }
    }

    result_size.* = @as(c_int, @intCast(count));
    return result.ptr;
}

// Thread context for parallel computation
const ThreadContext = struct {
    data: []const f64,
    start: usize,
    end: usize,
    result: *f64,
};

fn computeSum(context: *ThreadContext) void {
    var sum: f64 = 0.0;
    for (context.data[context.start..context.end]) |value| {
        sum += value;
    }
    context.result.* = sum;
}

export fn parallel_compute_ffi(data: [*]const f64, size: c_int, num_threads: c_int) f64 {
    const n = @as(usize, @intCast(size));
    var threads_count = @as(usize, @intCast(num_threads));

    if (n == 0) return 0.0;
    if (threads_count == 0) threads_count = 1;
    if (threads_count > n) threads_count = n;

    const data_slice = data[0..n];

    // For single thread, compute directly
    if (threads_count == 1) {
        var sum: f64 = 0.0;
        for (data_slice) |value| {
            sum += value;
        }
        return sum;
    }

    // Multi-threaded computation
    var threads = allocator.alloc(Thread, threads_count) catch {
        // Fallback to single-threaded if allocation fails
        var sum: f64 = 0.0;
        for (data_slice) |value| {
            sum += value;
        }
        return sum;
    };
    defer allocator.free(threads);

    var contexts = allocator.alloc(ThreadContext, threads_count) catch {
        // Fallback to single-threaded if allocation fails
        var sum: f64 = 0.0;
        for (data_slice) |value| {
            sum += value;
        }
        return sum;
    };
    defer allocator.free(contexts);

    var results = allocator.alloc(f64, threads_count) catch {
        // Fallback to single-threaded if allocation fails
        var sum: f64 = 0.0;
        for (data_slice) |value| {
            sum += value;
        }
        return sum;
    };
    defer allocator.free(results);

    const chunk_size = n / threads_count;
    
    // Create and start threads
    for (0..threads_count) |i| {
        const start = i * chunk_size;
        const end = if (i == threads_count - 1) n else (i + 1) * chunk_size;
        
        contexts[i] = ThreadContext{
            .data = data_slice,
            .start = start,
            .end = end,
            .result = &results[i],
        };
        
        threads[i] = Thread.spawn(.{}, computeSum, .{&contexts[i]}) catch {
            // If thread creation fails, compute sequentially for this chunk
            var sum: f64 = 0.0;
            for (data_slice[start..end]) |value| {
                sum += value;
            }
            results[i] = sum;
            continue;
        };
    }

    // Wait for all threads to complete
    for (threads) |thread| {
        thread.join();
    }

    // Sum all partial results
    var total_sum: f64 = 0.0;
    for (results) |partial_sum| {
        total_sum += partial_sum;
    }

    return total_sum;
}

export fn free_memory_ffi(ptr: ?*anyopaque) void {
    if (ptr) |p| {
        // Note: In a real implementation, we'd need to track allocation sizes
        // For now, we'll rely on Zig's allocator to handle this
        // This is a simplified version - in production, proper memory tracking would be needed
        _ = p; // Suppress unused variable warning
        // allocator.free(...) would be called here with proper size tracking
    }
}
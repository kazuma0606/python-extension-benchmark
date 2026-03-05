const std = @import("std");
const math = std.math;
const ArrayList = std.ArrayList;
const Allocator = std.mem.Allocator;
const Thread = std.Thread;

// Global allocator for C interface
var gpa = std.heap.GeneralPurposeAllocator(.{}){};
const allocator = gpa.allocator();

// Export functions for C ABI compatibility
export fn find_primes(n: c_int, result: [*]c_int, count: *c_int) void {
    const limit = @as(usize, @intCast(n));
    if (limit < 2) {
        count.* = 0;
        return;
    }

    // Sieve of Eratosthenes with memory-safe implementation
    var sieve = allocator.alloc(bool, limit + 1) catch {
        count.* = 0;
        return;
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

    // Collect primes
    var prime_count: usize = 0;
    for (sieve, 0..) |is_prime, idx| {
        if (is_prime) {
            result[prime_count] = @as(c_int, @intCast(idx));
            prime_count += 1;
        }
    }

    count.* = @as(c_int, @intCast(prime_count));
}

export fn matrix_multiply(
    a: [*]const f64, rows_a: c_int, cols_a: c_int,
    b: [*]const f64, rows_b: c_int, cols_b: c_int,
    result: [*]f64
) void {
    const ra = @as(usize, @intCast(rows_a));
    const ca = @as(usize, @intCast(cols_a));
    const rb = @as(usize, @intCast(rows_b));
    const cb = @as(usize, @intCast(cols_b));

    // Ensure dimensions are compatible
    if (ca != rb) return;

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
}export 
fn sort_array(arr: [*]c_int, length: c_int) void {
    const n = @as(usize, @intCast(length));
    if (n <= 1) return;

    // Convert to Zig slice for memory safety
    const slice = arr[0..n];
    
    // Use Zig's standard library sort (introsort - hybrid of quicksort, heapsort, and insertion sort)
    std.sort.heap(c_int, slice, {}, comptime std.sort.asc(c_int));
}

export fn filter_array(arr: [*]const c_int, length: c_int, threshold: c_int, result: [*]c_int, count: *c_int) void {
    const n = @as(usize, @intCast(length));
    const thresh = threshold;

    if (n == 0) {
        count.* = 0;
        return;
    }

    // Memory-safe filtering
    const input_slice = arr[0..n];
    var result_count: usize = 0;

    for (input_slice) |value| {
        if (value >= thresh) {
            result[result_count] = value;
            result_count += 1;
        }
    }

    count.* = @as(c_int, @intCast(result_count));
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

export fn parallel_compute(data: [*]const f64, length: c_int, num_threads: c_int) f64 {
    const n = @as(usize, @intCast(length));
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
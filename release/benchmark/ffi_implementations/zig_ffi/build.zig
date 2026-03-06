const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Create a shared library for FFI
    const lib = b.addSharedLibrary(.{
        .name = "libfunctions",
        .root_source_file = b.path("functions.zig"),
        .target = target,
        .optimize = optimize,
    });

    // Link with C library for FFI compatibility
    lib.linkLibC();
    
    // Install the library
    b.installArtifact(lib);
}
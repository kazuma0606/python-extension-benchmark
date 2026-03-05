# Python Extension Benchmark Docker Environment - Multi-Language Support
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for all build tools
RUN apt-get update && apt-get install -y \
    # C/C++ compiler and build tools
    gcc \
    g++ \
    make \
    cmake \
    # Fortran compiler
    gfortran \
    # Python development headers
    python3-dev \
    # Additional build dependencies
    build-essential \
    pkg-config \
    # Git for potential dependency installations
    git \
    # Curl for downloading language runtimes
    curl \
    # Unzip for extracting archives
    unzip \
    # Additional utilities
    wget \
    # Clean up apt cache
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for Rust extensions)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Verify Rust installation
RUN rustc --version && cargo --version

# Install Julia (for Julia extensions)
RUN curl -fsSL https://install.julialang.org | sh -s -- --yes
ENV PATH="/root/.juliaup/bin:${PATH}"

# Verify Julia installation and install required packages
RUN julia --version && \
    julia -e 'using Pkg; Pkg.add(["PyCall", "PythonCall"])'

# Install Go (for Go extensions)
RUN curl -fsSL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz | tar -C /usr/local -xzf -
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/root/go"
ENV GOBIN="/root/go/bin"

# Verify Go installation
RUN go version

# Install Zig (for Zig extensions)
RUN curl -fsSL https://ziglang.org/download/0.11.0/zig-linux-x86_64-0.11.0.tar.xz | tar -C /usr/local -xJf - && \
    ln -s /usr/local/zig-linux-x86_64-0.11.0/zig /usr/local/bin/zig
ENV PATH="/usr/local/zig-linux-x86_64-0.11.0:${PATH}"

# Verify Zig installation
RUN zig version

# Install Nim (for Nim extensions)
RUN curl -fsSL https://nim-lang.org/choosenim/init.sh | sh -s -- -y
ENV PATH="/root/.nimble/bin:${PATH}"

# Verify Nim installation and install nimpy
RUN nim --version && \
    nimble install -y nimpy

# Install Kotlin/Native (for Kotlin extensions)
RUN curl -fsSL https://github.com/JetBrains/kotlin/releases/download/v1.9.21/kotlin-native-linux-x86_64-1.9.21.tar.gz | tar -C /usr/local -xzf - && \
    ln -s /usr/local/kotlin-native-linux-x86_64-1.9.21/bin/kotlinc-native /usr/local/bin/kotlinc-native && \
    ln -s /usr/local/kotlin-native-linux-x86_64-1.9.21/bin/kotlin /usr/local/bin/kotlin
ENV PATH="/usr/local/kotlin-native-linux-x86_64-1.9.21/bin:${PATH}"

# Install Gradle (for Kotlin builds)
RUN curl -fsSL https://services.gradle.org/distributions/gradle-8.5-bin.zip -o gradle.zip && \
    unzip gradle.zip -d /usr/local && \
    ln -s /usr/local/gradle-8.5/bin/gradle /usr/local/bin/gradle && \
    rm gradle.zip
ENV PATH="/usr/local/gradle-8.5/bin:${PATH}"

# Verify Kotlin/Native and Gradle installation
RUN kotlin -version && gradle --version

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional Python build dependencies
RUN pip install --no-cache-dir \
    wheel \
    maturin \
    setuptools-rust \
    hypothesis

# Copy the entire project
COPY . .

# Build all extension modules in optimized order
# Start with simpler extensions first

# 1. Build C extensions (baseline)
RUN echo "Building C extensions..." && \
    cd benchmark/c_ext && python setup.py build_ext --inplace && cd ../.. || \
    echo "⚠️ C extension build failed, continuing..."

# 2. Build C++ extensions
RUN echo "Building C++ extensions..." && \
    python scripts/build/build_cpp_ext.py || \
    echo "⚠️ C++ extension build failed, continuing..."

# 3. Build Rust extensions
RUN echo "Building Rust extensions..." && \
    python scripts/build/build_rust_ext.py || \
    echo "⚠️ Rust extension build failed, continuing..."

# 4. Build Fortran extensions
RUN echo "Building Fortran extensions..." && \
    python scripts/build/build_fortran_ext.py || \
    echo "⚠️ Fortran extension build failed, continuing..."

# 5. Build Julia extensions
RUN echo "Building Julia extensions..." && \
    python scripts/build/build_julia_ext.py || \
    echo "⚠️ Julia extension build failed, continuing..."

# 6. Build Go extensions
RUN echo "Building Go extensions..." && \
    python scripts/build/build_go_ext.py || \
    echo "⚠️ Go extension build failed, continuing..."

# 7. Build Zig extensions
RUN echo "Building Zig extensions..." && \
    python scripts/build/build_zig_ext.py || \
    echo "⚠️ Zig extension build failed, continuing..."

# 8. Build Nim extensions
RUN echo "Building Nim extensions..." && \
    python scripts/build/build_nim_ext.py || \
    echo "⚠️ Nim extension build failed, continuing..."

# 9. Build Kotlin extensions
RUN echo "Building Kotlin extensions..." && \
    python scripts/build/build_kotlin_ext.py || \
    echo "⚠️ Kotlin extension build failed, continuing..."

# Skip Cython for now to avoid conflicts
# RUN echo "Building Cython extensions..." && \
#     python scripts/build/build_cython.py || \
#     echo "⚠️ Cython extension build failed, continuing..."

# Set environment variables for optimal performance
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Set thread limits for consistent benchmarking
ENV OMP_NUM_THREADS=4
ENV NUMBA_NUM_THREADS=4
ENV MKL_NUM_THREADS=4
ENV JULIA_NUM_THREADS=4

# Create results directory
RUN mkdir -p benchmark/results/{json,csv,graphs}

# Add a health check script
RUN echo '#!/bin/bash\n\
echo "=== Multi-Language Extension Health Check ==="\n\
echo "Python: $(python --version)"\n\
echo "Rust: $(rustc --version 2>/dev/null || echo "Not available")"\n\
echo "Julia: $(julia --version 2>/dev/null || echo "Not available")"\n\
echo "Go: $(go version 2>/dev/null || echo "Not available")"\n\
echo "Zig: $(zig version 2>/dev/null || echo "Not available")"\n\
echo "Nim: $(nim --version 2>/dev/null | head -1 || echo "Not available")"\n\
echo "Kotlin: $(kotlin -version 2>/dev/null || echo "Not available")"\n\
echo ""\n\
echo "=== Testing Python imports ==="\n\
python -c "import benchmark.python; print(\"✓ Python implementation\")" 2>/dev/null || echo "✗ Python implementation"\n\
python -c "import benchmark.numpy_impl; print(\"✓ NumPy implementation\")" 2>/dev/null || echo "✗ NumPy implementation"\n\
python -c "import benchmark.c_ext; print(\"✓ C extension\")" 2>/dev/null || echo "✗ C extension"\n\
python -c "import benchmark.cpp_ext; print(\"✓ C++ extension\")" 2>/dev/null || echo "✗ C++ extension"\n\
python -c "import benchmark.rust_ext; print(\"✓ Rust extension\")" 2>/dev/null || echo "✗ Rust extension"\n\
python -c "import benchmark.fortran_ext; print(\"✓ Fortran extension\")" 2>/dev/null || echo "✗ Fortran extension"\n\
python -c "import benchmark.julia_ext; print(\"✓ Julia extension\")" 2>/dev/null || echo "✗ Julia extension"\n\
python -c "import benchmark.go_ext; print(\"✓ Go extension\")" 2>/dev/null || echo "✗ Go extension"\n\
python -c "import benchmark.zig_ext; print(\"✓ Zig extension\")" 2>/dev/null || echo "✗ Zig extension"\n\
python -c "import benchmark.nim_ext; print(\"✓ Nim extension\")" 2>/dev/null || echo "✗ Nim extension"\n\
python -c "import benchmark.kotlin_ext; print(\"✓ Kotlin extension\")" 2>/dev/null || echo "✗ Kotlin extension"\n\
echo ""\n\
echo "=== Health Check Complete ==="\n\
' > /usr/local/bin/health-check && chmod +x /usr/local/bin/health-check

# Default command runs health check and then tests
CMD ["sh", "-c", "health-check && python -m pytest tests/ -v"]
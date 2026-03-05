# Python Extension Benchmark Docker Environment
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
    # Curl for downloading Rust
    curl \
    # Clean up apt cache
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Verify Rust installation
RUN rustc --version && cargo --version

# Install Julia
RUN curl -fsSL https://install.julialang.org | sh -s -- --yes
ENV PATH="/root/.juliaup/bin:${PATH}"

# Verify Julia installation
RUN julia --version

# Install Go
RUN curl -fsSL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz | tar -C /usr/local -xzf -
ENV PATH="/usr/local/go/bin:${PATH}"

# Verify Go installation
RUN go version

# Install Zig
RUN curl -fsSL https://ziglang.org/download/0.15.2/zig-linux-x86_64-0.15.2.tar.xz | tar -C /usr/local -xJf - && \
    ln -s /usr/local/zig-linux-x86_64-0.15.2/zig /usr/local/bin/zig
ENV PATH="/usr/local/zig-linux-x86_64-0.15.2:${PATH}"

# Verify Zig installation
RUN zig version

# Install Nim
RUN curl -fsSL https://nim-lang.org/choosenim/init.sh | sh -s -- -y
ENV PATH="/root/.nimble/bin:${PATH}"

# Verify Nim installation
RUN nim --version

# Install Kotlin/Native
RUN curl -fsSL https://github.com/JetBrains/kotlin/releases/download/v1.9.21/kotlin-native-linux-x86_64-1.9.21.tar.gz | tar -C /usr/local -xzf - && \
    ln -s /usr/local/kotlin-native-linux-x86_64-1.9.21/bin/kotlinc-native /usr/local/bin/kotlinc-native && \
    ln -s /usr/local/kotlin-native-linux-x86_64-1.9.21/bin/kotlin /usr/local/bin/kotlin
ENV PATH="/usr/local/kotlin-native-linux-x86_64-1.9.21/bin:${PATH}"

# Install Gradle
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
    setuptools-rust

# Copy the entire project
COPY . .

# Build all extension modules
RUN echo "Building C extensions..." && \
    cd benchmark/c_ext && python setup.py build_ext --inplace && cd ../..

RUN echo "Building C++ extensions..." && \
    python scripts/build/build_cpp_ext.py

# Skip Cython for now to test Fortran
# RUN echo "Building Cython extensions..." && \
#     python scripts/build/build_cython.py

RUN echo "Building Rust extensions..." && \
    python scripts/build/build_rust_ext.py

RUN echo "Building Fortran extensions..." && \
    python scripts/build/build_fortran_ext.py

RUN echo "Building Julia extensions..." && \
    python scripts/build/build_julia_ext.py

RUN echo "Building Go extensions..." && \
    python scripts/build/build_go_ext.py

RUN echo "Building Zig extensions..." && \
    python scripts/build/build_zig_ext.py

RUN echo "Building Nim extensions..." && \
    python scripts/build/build_nim_ext.py

RUN echo "Building Kotlin extensions..." && \
    python scripts/build/build_kotlin_ext.py

# Set environment variables for optimal performance
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create results directory
RUN mkdir -p benchmark/results/{json,csv,graphs}

# Default command
CMD ["python", "-m", "pytest", "tests/", "-v"]
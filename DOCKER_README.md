# Docker Environment for Python Extension Benchmark

This document describes how to use the Docker environment for the Python Extension Benchmark project.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available for Docker
- At least 4 CPU cores recommended

## Quick Start

### Build and Run Tests

```bash
# Build the Docker image and run tests
docker-compose up test

# Or build and run interactively
docker-compose up benchmark
```

### Interactive Development

```bash
# Start interactive container
docker-compose run --rm benchmark

# Inside the container, you can run:
python -m pytest tests/ -v
python demo_error_handling.py
```

## Services

### `benchmark`
- **Purpose**: Main development and benchmarking service
- **Resources**: 4 CPU cores, 8GB RAM
- **Use case**: Full benchmark runs with optimal performance

### `benchmark-limited`
- **Purpose**: Resource-constrained testing
- **Resources**: 2 CPU cores, 4GB RAM  
- **Use case**: Testing scalability and performance under constraints

### `test`
- **Purpose**: Automated testing
- **Resources**: 2 CPU cores, 4GB RAM
- **Use case**: CI/CD and automated test runs

## Running Benchmarks

```bash
# Run full benchmark suite
docker-compose run --rm benchmark python -c "
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import get_all_scenarios
runner = BenchmarkRunner()
results = runner.run_all_scenarios()
print('Benchmark completed!')
"

# Run specific tests
docker-compose run --rm benchmark python -m pytest tests/test_scenarios.py -v

# Run with resource limits
docker-compose run --rm benchmark-limited python -m pytest tests/ -v
```

## Volume Mounts

- `./benchmark/results` → `/app/benchmark/results`: Persistent benchmark results
- `./benchmark` → `/app/benchmark`: Source code (for development)
- `./tests` → `/app/tests`: Test files

## Environment Variables

- `PYTHONPATH=/app`: Python module path
- `PYTHONUNBUFFERED=1`: Unbuffered Python output
- `OMP_NUM_THREADS`: OpenMP thread limit
- `NUMBA_NUM_THREADS`: Numba thread limit  
- `MKL_NUM_THREADS`: Intel MKL thread limit

## Build Process

The Docker image automatically builds all extension modules:

1. **C Extensions**: Built using `python setup.py build_ext --inplace`
2. **C++ Extensions**: Built using CMake and pybind11
3. **Cython Extensions**: Built using `python build_cython.py`
4. **Rust Extensions**: Built using `python build_rust_ext.py`

## Troubleshooting

### Build Failures

```bash
# Rebuild without cache
docker-compose build --no-cache

# Check build logs
docker-compose build benchmark 2>&1 | tee build.log
```

### Memory Issues

```bash
# Increase Docker memory limit in Docker Desktop settings
# Or use the limited service
docker-compose run --rm benchmark-limited
```

### Permission Issues

```bash
# Fix result directory permissions
sudo chown -R $USER:$USER benchmark/results/
```

## Performance Considerations

- The container limits CPU and memory for consistent benchmarking
- Thread limits are set via environment variables
- Results are persisted to host filesystem via volume mounts
- Build artifacts are created fresh in each container for consistency

## Development Workflow

1. Make code changes on host
2. Run tests in container: `docker-compose run --rm test`
3. Run benchmarks: `docker-compose run --rm benchmark`
4. Results are saved to `./benchmark/results/` on host

## Cleaning Up

```bash
# Remove containers
docker-compose down

# Remove images
docker-compose down --rmi all

# Remove volumes
docker-compose down --volumes
```
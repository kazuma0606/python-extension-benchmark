# Makefile for building Go shared library for Python integration

# Detect operating system
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    LIB_EXT = so
    LIB_NAME = libgofunctions.so
endif
ifeq ($(UNAME_S),Darwin)
    LIB_EXT = dylib
    LIB_NAME = libgofunctions.dylib
endif
ifeq ($(OS),Windows_NT)
    LIB_EXT = dll
    LIB_NAME = libgofunctions.dll
endif

# Default target
all: $(LIB_NAME)

# Build shared library
$(LIB_NAME): functions.go
	@echo "Building Go shared library: $(LIB_NAME)"
	go build -buildmode=c-shared -o $(LIB_NAME) functions.go
	@echo "Go shared library built successfully"

# Clean build artifacts
clean:
	rm -f *.so *.dylib *.dll *.h
	@echo "Cleaned build artifacts"

# Install dependencies (if any)
deps:
	go mod tidy
	@echo "Dependencies updated"

# Test the library (basic compilation test)
test: $(LIB_NAME)
	@echo "Testing Go library compilation..."
	@if [ -f "$(LIB_NAME)" ]; then \
		echo "✓ Shared library exists"; \
		file $(LIB_NAME) 2>/dev/null || echo "✓ Library file created"; \
	else \
		echo "✗ Shared library not found"; \
		exit 1; \
	fi

# Force rebuild
rebuild: clean all

.PHONY: all clean deps test rebuild
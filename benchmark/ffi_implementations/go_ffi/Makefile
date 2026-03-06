# Makefile for building Go FFI shared library

# Detect operating system
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    LIB_EXT = so
    LIB_NAME = libfunctions.so
endif
ifeq ($(UNAME_S),Darwin)
    LIB_EXT = dylib
    LIB_NAME = libfunctions.dylib
endif
ifeq ($(OS),Windows_NT)
    LIB_EXT = dll
    LIB_NAME = libfunctions.dll
endif

# Default target
all: $(LIB_NAME)

# Build shared library
$(LIB_NAME): functions.go go.mod
	@echo "Building Go FFI shared library: $(LIB_NAME)"
	go build -buildmode=c-shared -o $(LIB_NAME) functions.go
	@echo "Go FFI shared library built successfully"

# Clean build artifacts
clean:
	rm -f *.so *.dylib *.dll *.h
	@echo "Cleaned Go FFI build artifacts"

# Install dependencies
deps:
	go mod tidy
	@echo "Go FFI dependencies updated"

# Test the library (basic compilation test)
test: $(LIB_NAME)
	@echo "Testing Go FFI library compilation..."
	@if [ -f "$(LIB_NAME)" ]; then \
		echo "✓ Go FFI shared library exists"; \
		file $(LIB_NAME) 2>/dev/null || echo "✓ Go FFI library file created"; \
	else \
		echo "✗ Go FFI shared library not found"; \
		exit 1; \
	fi

# Force rebuild
rebuild: clean all

# Build for specific platform
linux:
	GOOS=linux GOARCH=amd64 go build -buildmode=c-shared -o libfunctions.so functions.go

windows:
	GOOS=windows GOARCH=amd64 go build -buildmode=c-shared -o libfunctions.dll functions.go

darwin:
	GOOS=darwin GOARCH=amd64 go build -buildmode=c-shared -o libfunctions.dylib functions.go

.PHONY: all clean deps test rebuild linux windows darwin
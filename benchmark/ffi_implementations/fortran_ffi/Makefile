# Makefile for Fortran FFI shared library
# Builds a C ABI compatible shared library from Fortran source

# Compiler and flags
FC = gfortran
FFLAGS = -fPIC -O3 -fopenmp -std=f2008
LDFLAGS = -shared -fopenmp

# Platform-specific settings
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    TARGET = libfortranfunctions.so
    FFLAGS += -fno-underscoring
endif
ifeq ($(UNAME_S),Darwin)
    TARGET = libfortranfunctions.dylib
    FFLAGS += -fno-underscoring
endif
ifeq ($(OS),Windows_NT)
    TARGET = libfortranfunctions.dll
    FFLAGS += -fno-underscoring
endif

# Source files
SOURCES = functions.f90
OBJECTS = $(SOURCES:.f90=.o)

# Default target
all: $(TARGET)

# Build shared library
$(TARGET): $(OBJECTS)
	$(FC) $(LDFLAGS) -o $@ $^

# Compile Fortran source
%.o: %.f90
	$(FC) $(FFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f *.o *.mod $(TARGET)

# Install (copy to current directory)
install: $(TARGET)
	@echo "Fortran FFI library built successfully: $(TARGET)"

# Test if gfortran is available
check:
	@which gfortran > /dev/null || (echo "Error: gfortran not found. Please install gfortran." && exit 1)
	@echo "gfortran found: $$(gfortran --version | head -n1)"

# Help
help:
	@echo "Available targets:"
	@echo "  all     - Build the shared library (default)"
	@echo "  clean   - Remove build artifacts"
	@echo "  install - Build and confirm installation"
	@echo "  check   - Check if gfortran is available"
	@echo "  help    - Show this help message"

.PHONY: all clean install check help
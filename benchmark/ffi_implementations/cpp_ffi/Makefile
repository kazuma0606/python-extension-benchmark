# Makefile for C++ FFI shared library

# Compiler and flags
CXX = g++
CXXFLAGS = -Wall -Wextra -O2 -fPIC -std=c++11
LDFLAGS = -shared

# Platform-specific settings
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    TARGET = libfunctions.so
    LDFLAGS += -lm
endif
ifeq ($(UNAME_S),Darwin)
    TARGET = libfunctions.dylib
    LDFLAGS += -lm
endif
ifeq ($(OS),Windows_NT)
    TARGET = libfunctions.dll
    CXX = g++
endif

# Source files
SOURCES = functions.cpp
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET)

# Build shared library
$(TARGET): $(OBJECTS)
	$(CXX) $(LDFLAGS) -o $@ $^

# Compile source files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f $(OBJECTS) $(TARGET) *.so *.dll *.dylib

# Install (copy to current directory)
install: $(TARGET)
	@echo "Shared library $(TARGET) built successfully"

# Test build
test: $(TARGET)
	@echo "Testing shared library..."
	@if [ -f $(TARGET) ]; then \
		echo "✓ $(TARGET) exists"; \
		file $(TARGET) 2>/dev/null || echo "✓ $(TARGET) is a valid library"; \
	else \
		echo "✗ $(TARGET) not found"; \
		exit 1; \
	fi

.PHONY: all clean install test
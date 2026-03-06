#!/bin/bash
# Build script for Kotlin FFI implementation

echo "Building Kotlin FFI shared library..."

# Check if Gradle is available
if command -v gradle &> /dev/null; then
    echo "Using system Gradle"
    gradle build
elif [ -f "./gradlew" ]; then
    echo "Using Gradle wrapper"
    ./gradlew build
else
    echo "Gradle not found. Please install Gradle or use the Gradle wrapper."
    echo "You can download Gradle from: https://gradle.org/install/"
    echo ""
    echo "Alternative: Download Gradle wrapper files:"
    echo "  gradle/wrapper/gradle-wrapper.jar"
    echo "  gradle/wrapper/gradle-wrapper.properties"
    echo "  gradlew (Unix)"
    echo "  gradlew.bat (Windows)"
    exit 1
fi

echo "Kotlin FFI build completed."
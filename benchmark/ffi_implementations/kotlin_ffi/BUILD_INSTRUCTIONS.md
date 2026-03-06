# Kotlin FFI Build Instructions

The Kotlin FFI implementation is ready but requires Gradle and Kotlin/Native toolchain to build.

## Quick Setup

1. **Install JDK 8+**:
   - Download from https://adoptium.net/
   - Set JAVA_HOME environment variable

2. **Install Gradle**:
   - Download from https://gradle.org/install/
   - Add to PATH

3. **Build the library**:
   ```bash
   gradle build
   ```

## Alternative: Use Gradle Wrapper

If you prefer not to install Gradle globally:

1. Download Gradle wrapper files to this directory:
   - `gradle/wrapper/gradle-wrapper.jar`
   - `gradle/wrapper/gradle-wrapper.properties`
   - `gradlew` (Unix) or `gradlew.bat` (Windows)

2. Build using wrapper:
   ```bash
   ./gradlew build    # Unix
   gradlew.bat build  # Windows
   ```

## Expected Output

After successful build, you should see:
- `liblibfunctions.dll` (Windows)
- `liblibfunctions.so` (Linux)  
- `liblibfunctions.dylib` (macOS)

## Troubleshooting

- **JAVA_HOME not set**: Ensure JDK is installed and JAVA_HOME points to it
- **Gradle not found**: Install Gradle or use wrapper
- **Build fails**: Check that all dependencies are available

The Kotlin FFI implementation will be automatically detected by the benchmark system once the shared library is built.
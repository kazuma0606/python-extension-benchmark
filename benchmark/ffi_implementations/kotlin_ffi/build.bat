@echo off
REM Build script for Kotlin FFI implementation

echo Building Kotlin FFI shared library...

REM Check if Gradle is available
where gradle >nul 2>nul
if %ERRORLEVEL% == 0 (
    echo Using system Gradle
    gradle build
) else if exist "gradlew.bat" (
    echo Using Gradle wrapper
    gradlew.bat build
) else (
    echo Gradle not found. Please install Gradle or use the Gradle wrapper.
    echo You can download Gradle from: https://gradle.org/install/
    echo.
    echo Alternative: Download Gradle wrapper files:
    echo   gradle/wrapper/gradle-wrapper.jar
    echo   gradle/wrapper/gradle-wrapper.properties
    echo   gradlew (Unix)
    echo   gradlew.bat (Windows)
    exit /b 1
)

echo Kotlin FFI build completed.
@echo off
REM Common build script template for FFI implementations (Windows)
REM This script should be customized for each language implementation

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%i in ("%SCRIPT_DIR%.") do set "LANGUAGE_NAME=%%~ni"

echo Building FFI implementation for: %LANGUAGE_NAME%

REM Check if uv environment is active
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: uv virtual environment is not active!
    echo Please activate uv environment with: uv sync ^&^& .venv\Scripts\activate
    exit /b 1
)

if not "%VIRTUAL_ENV%"=="%VIRTUAL_ENV:.venv=%" (
    echo uv environment detected: %VIRTUAL_ENV%
) else (
    echo WARNING: Virtual environment may not be uv-managed!
    echo Please ensure you're using uv environment
)

REM Language-specific build commands should be added here
REM Examples:
REM For C: gcc -shared -fPIC -o functions.dll functions.c
REM For Rust: cargo build --release --lib
REM For Go: go build -buildmode=c-shared -o functions.dll functions.go

echo Build template - customize this script for %LANGUAGE_NAME%
echo Add your language-specific build commands here

REM Verify shared library was created
set "EXPECTED_LIB=functions.dll"
if not exist "%EXPECTED_LIB%" (
    echo ERROR: Expected shared library %EXPECTED_LIB% was not created
    exit /b 1
)

echo Build completed successfully for %LANGUAGE_NAME%
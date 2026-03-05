"""
Build Script Generator
Generates build scripts for different platforms and engines.
"""

from typing import Dict, List, Optional, Any
from enum import Enum


class BuildScriptGenerator:
    """Generates build scripts for game projects."""
    
    @staticmethod
    def generate_unity_batch_build() -> str:
        """Generate Unity batch build script (Windows)."""
        return '''@echo off
REM Unity Batch Build Script
REM Usage: build.bat [platform] [build_type]

set UNITY_PATH="C:\\Program Files\\Unity\\Hub\\Editor\\2022.3.0f1\\Editor\\Unity.exe"
set PROJECT_PATH=%cd%
set BUILD_PATH=%PROJECT_PATH%\\Builds

if not exist "%BUILD_PATH%" mkdir "%BUILD_PATH%"

set PLATFORM=%1
set BUILD_TYPE=%2

if "%PLATFORM%"=="" set PLATFORM=windows
if "%BUILD_TYPE%"=="" set BUILD_TYPE=development

echo Building for %PLATFORM% (%BUILD_TYPE%)...

if "%PLATFORM%"=="windows" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneWindows64 -executeMethod BuildScript.BuildWindows64 -logFile "%BUILD_PATH%\\build_windows.log"
) else if "%PLATFORM%"=="mac" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneOSX -executeMethod BuildScript.BuildMac -logFile "%BUILD_PATH%\\build_mac.log"
) else if "%PLATFORM%"=="linux" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneLinux64 -executeMethod BuildScript.BuildLinux64 -logFile "%BUILD_PATH%\\build_linux.log"
) else if "%PLATFORM%"=="android" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget Android -executeMethod BuildScript.BuildAndroid -logFile "%BUILD_PATH%\\build_android.log"
) else if "%PLATFORM%"=="ios" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget iOS -executeMethod BuildScript.BuildiOS -logFile "%BUILD_PATH%\\build_ios.log"
) else if "%PLATFORM%"=="webgl" (
    %UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget WebGL -executeMethod BuildScript.BuildWebGL -logFile "%BUILD_PATH%\\build_webgl.log"
) else if "%PLATFORM%"=="all" (
    call :build_windows
    call :build_mac
    call :build_linux
) else (
    echo Unknown platform: %PLATFORM%
    echo Usage: build.bat [windows^|mac^|linux^|android^|ios^|webgl^|all] [development^|release]
    exit /b 1
)

echo Build complete!
exit /b 0

:build_windows
%UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneWindows64 -executeMethod BuildScript.BuildWindows64 -logFile "%BUILD_PATH%\\build_windows.log"
exit /b 0

:build_mac
%UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneOSX -executeMethod BuildScript.BuildMac -logFile "%BUILD_PATH%\\build_mac.log"
exit /b 0

:build_linux
%UNITY_PATH% -batchmode -nographics -quit -projectPath "%PROJECT_PATH%" -buildTarget StandaloneLinux64 -executeMethod BuildScript.BuildLinux64 -logFile "%BUILD_PATH%\\build_linux.log"
exit /b 0
'''
    
    @staticmethod
    def generate_unity_shell_build() -> str:
        """Generate Unity shell build script (Mac/Linux)."""
        return '''#!/bin/bash
# Unity Shell Build Script
# Usage: ./build.sh [platform] [build_type]

UNITY_PATH="/Applications/Unity/Hub/Editor/2022.3.0f1/Unity.app/Contents/MacOS/Unity"
PROJECT_PATH="$(pwd)"
BUILD_PATH="$PROJECT_PATH/Builds"

# Create build directory
mkdir -p "$BUILD_PATH"

PLATFORM=${1:-windows}
BUILD_TYPE=${2:-development}

echo "Building for $PLATFORM ($BUILD_TYPE)..."

case "$PLATFORM" in
    "windows")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneWindows64 -executeMethod BuildScript.BuildWindows64 -logFile "$BUILD_PATH/build_windows.log"
        ;;
    "mac")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneOSX -executeMethod BuildScript.BuildMac -logFile "$BUILD_PATH/build_mac.log"
        ;;
    "linux")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneLinux64 -executeMethod BuildScript.BuildLinux64 -logFile "$BUILD_PATH/build_linux.log"
        ;;
    "android")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget Android -executeMethod BuildScript.BuildAndroid -logFile "$BUILD_PATH/build_android.log"
        ;;
    "ios")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget iOS -executeMethod BuildScript.BuildiOS -logFile "$BUILD_PATH/build_ios.log"
        ;;
    "webgl")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget WebGL -executeMethod BuildScript.BuildWebGL -logFile "$BUILD_PATH/build_webgl.log"
        ;;
    "all")
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneWindows64 -executeMethod BuildScript.BuildWindows64 -logFile "$BUILD_PATH/build_windows.log"
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneOSX -executeMethod BuildScript.BuildMac -logFile "$BUILD_PATH/build_mac.log"
        "$UNITY_PATH" -batchmode -nographics -quit -projectPath "$PROJECT_PATH" -buildTarget StandaloneLinux64 -executeMethod BuildScript.BuildLinux64 -logFile "$BUILD_PATH/build_linux.log"
        ;;
    *)
        echo "Unknown platform: $PLATFORM"
        echo "Usage: $0 [windows|mac|linux|android|ios|webgl|all] [development|release]"
        exit 1
        ;;
esac

echo "Build complete!"
'''
    
    @staticmethod
    def generate_godot_export_script() -> str:
        """Generate Godot export script."""
        return '''#!/bin/bash
# Godot Export Script
# Usage: ./export.sh [platform]

GODOT_PATH="/usr/bin/godot"
PROJECT_PATH="$(pwd)"
BUILD_PATH="$PROJECT_PATH/Builds"

# Create build directory
mkdir -p "$BUILD_PATH"

export_platform() {
    local platform=$1
    local preset=$2
    local output=$3
    
    echo "Exporting for $platform..."
    $GODOT_PATH --headless --path "$PROJECT_PATH" --export-release "$preset" "$BUILD_PATH/$output"
    
    if [ $? -eq 0 ]; then
        echo "✓ $platform export successful"
    else
        echo "✗ $platform export failed"
    fi
}

case "$1" in
    "windows")
        export_platform "Windows" "Windows Desktop" "Windows/MyGame.exe"
        ;;
    "mac")
        export_platform "macOS" "macOS" "Mac/MyGame.zip"
        ;;
    "linux")
        export_platform "Linux" "Linux/X11" "Linux/MyGame.x86_64"
        ;;
    "android")
        export_platform "Android" "Android" "Android/MyGame.apk"
        ;;
    "ios")
        export_platform "iOS" "iOS" "iOS/MyGame.ipa"
        ;;
    "web")
        export_platform "Web" "Web" "Web/index.html"
        ;;
    "all"|"")
        export_platform "Windows" "Windows Desktop" "Windows/MyGame.exe"
        export_platform "macOS" "macOS" "Mac/MyGame.zip"
        export_platform "Linux" "Linux/X11" "Linux/MyGame.x86_64"
        ;;
    *)
        echo "Unknown platform: $1"
        echo "Usage: $0 [windows|mac|linux|android|ios|web|all]"
        exit 1
        ;;
esac

echo "Export complete!"
'''
    
    @staticmethod
    def generate_unreal_build_script() -> str:
        """Generate Unreal build script."""
        return '''#!/bin/bash
# Unreal Engine Build Script
# Usage: ./build.sh [platform] [configuration]

UE_PATH="/Users/Shared/Epic Games/UE_5.3"
PROJECT_PATH="$(pwd)"
PROJECT_NAME="MyGame"
BUILD_PATH="$PROJECT_PATH/Builds"

# Create build directory
mkdir -p "$BUILD_PATH"

PLATFORM=${1:-Win64}
CONFIG=${2:-Development}

echo "Building $PROJECT_NAME for $PLATFORM ($CONFIG)..."

# Run UAT build
"$UE_PATH/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \\
    -project="$PROJECT_PATH/$PROJECT_NAME.uproject" \\
    -platform=$PLATFORM \\
    -clientconfig=$CONFIG \\
    -serverconfig=$CONFIG \\
    -cook \\
    -build \\
    -stage \\
    -pak \\
    -archive \\
    -archivedirectory="$BUILD_PATH/$PLATFORM"

if [ $? -eq 0 ]; then
    echo "✓ Build successful"
else
    echo "✗ Build failed"
    exit 1
fi

echo "Build complete! Output: $BUILD_PATH/$PLATFORM"
'''
    
    @staticmethod
    def generate_dockerfile(engine: str = "unity") -> str:
        """Generate Dockerfile for game builds."""
        if engine == "unity":
            return '''FROM unityci/editor:ubuntu-2022.3.0f1-linux-il2cpp-1

# Set working directory
WORKDIR /project

# Copy project files
COPY . .

# Build the project
RUN unity-editor \\
    -batchmode \\
    -nographics \\
    -quit \\
    -projectPath /project \\
    -buildTarget StandaloneLinux64 \\
    -executeMethod BuildScript.BuildLinux64 \\
    -logFile /project/build.log

# Output directory
VOLUME ["/project/Builds"]
'''
        elif engine == "godot":
            return '''FROM barichello/godot-ci:4.2

# Set working directory
WORKDIR /project

# Copy project files
COPY . .

# Export the project
RUN mkdir -p /project/builds && \\
    godot --headless --verbose --export-release "Linux/X11" /project/builds/MyGame.x86_64

# Output directory
VOLUME ["/project/builds"]
'''
        else:
            return "# Dockerfile not available for this engine"
    
    @staticmethod
    def generate_makefile() -> str:
        """Generate Makefile for game builds."""
        return '''# Game Build Makefile
# Usage: make [target]

.PHONY: all clean windows mac linux android ios web

# Default target
all: windows mac linux

# Clean build directory
clean:
\trm -rf Builds/

# Windows build
windows:
\t@echo "Building for Windows..."
\t@mkdir -p Builds/Windows
\t@# Add build command here

# Mac build
mac:
\t@echo "Building for macOS..."
\t@mkdir -p Builds/Mac
\t@# Add build command here

# Linux build
linux:
\t@echo "Building for Linux..."
\t@mkdir -p Builds/Linux
\t@# Add build command here

# Android build
android:
\t@echo "Building for Android..."
\t@mkdir -p Builds/Android
\t@# Add build command here

# iOS build
ios:
\t@echo "Building for iOS..."
\t@mkdir -p Builds/iOS
\t@# Add build command here

# Web build
web:
\t@echo "Building for Web..."
\t@mkdir -p Builds/Web
\t@# Add build command here

# Help
help:
\t@echo "Available targets:"
\t@echo "  all      - Build for all platforms (default)"
\t@echo "  clean    - Clean build directory"
\t@echo "  windows  - Build for Windows"
\t@echo "  mac      - Build for macOS"
\t@echo "  linux    - Build for Linux"
\t@echo "  android  - Build for Android"
\t@echo "  ios      - Build for iOS"
\t@echo "  web      - Build for Web"
'''
    
    @staticmethod
    def generate_package_json_scripts() -> Dict[str, str]:
        """Generate npm-style package.json scripts for game builds."""
        return {
            "build": "npm run build:all",
            "build:all": "npm run build:windows && npm run build:mac && npm run build:linux",
            "build:windows": "echo 'Building for Windows...' && # Add build command",
            "build:mac": "echo 'Building for macOS...' && # Add build command",
            "build:linux": "echo 'Building for Linux...' && # Add build command",
            "build:android": "echo 'Building for Android...' && # Add build command",
            "build:ios": "echo 'Building for iOS...' && # Add build command",
            "build:web": "echo 'Building for Web...' && # Add build command",
            "clean": "rm -rf Builds/",
            "test": "echo 'Running tests...' && # Add test command",
            "deploy": "echo 'Deploying...' && # Add deploy command"
        }

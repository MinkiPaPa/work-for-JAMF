#!/bin/bash

# 이전 빌드 정리
rm -rf build dist

# Homebrew Python 경로 (Universal Binary)
PYTHON_PATH=$(brew --prefix python)/bin/python3

# 필요한 패키지 설치
$PYTHON_PATH -m pip install pyinstaller pyqt5

# Universal Binary 빌드
$PYTHON_PATH -m PyInstaller --clean --windowed --target-architecture universal2 --name="macOS Installer Downloader" macOSUpdate.py

echo "Build completed!"

# 바이너리 정보 확인
echo "Checking binary architecture..."
file dist/macOS\ Installer\ Downloader.app/Contents/MacOS/macOS\ Installer\ Downloader 
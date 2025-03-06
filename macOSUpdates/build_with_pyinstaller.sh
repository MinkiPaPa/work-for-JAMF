#!/bin/bash

# 이전 빌드 정리
rm -rf build dist

# PyInstaller 설치 (필요한 경우)
pip install pyinstaller

# x86_64 아키텍처로만 빌드
pyinstaller --clean --windowed --target-architecture x86_64 --name="macOS Installer Downloader" macOSUpdate.py

# 빌드 완료 확인
echo "Build completed!"

# 바이너리 정보 확인
echo "Checking binary architecture..."
file dist/macOS\ Installer\ Downloader.app/Contents/MacOS/macOS\ Installer\ Downloader 
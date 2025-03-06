#!/bin/bash

# 이전 빌드 정리
rm -rf build dist

# PyInstaller 설치
pip install pyinstaller

# Intel(x86_64) 버전 빌드
echo "Building x86_64 version..."
pyinstaller --clean --windowed --target-architecture x86_64 --name="macOS Installer Downloader" macOSUpdate.py

# 빌드된 앱 이름 변경
mv dist/macOS\ Installer\ Downloader.app dist/macOS\ Installer\ Downloader-x86_64.app

# 앱 복사본 생성 (Universal Binary용)
cp -R dist/macOS\ Installer\ Downloader-x86_64.app dist/macOS\ Installer\ Downloader.app

echo "Build completed!"
echo "Note: This is an x86_64 binary that will run on Apple Silicon using Rosetta 2"

# 바이너리 정보 확인
echo "Checking binary architecture..."
file dist/macOS\ Installer\ Downloader.app/Contents/MacOS/macOS\ Installer\ Downloader 
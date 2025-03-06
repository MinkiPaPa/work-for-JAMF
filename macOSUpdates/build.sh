#!/bin/bash

# 이전 빌드 정리
rm -rf build dist

# 환경 변수 설정
export DYLD_LIBRARY_PATH=$(brew --prefix libffi)/lib:$DYLD_LIBRARY_PATH

# Python 경로 확인
PYTHON_PATH=$(which python)
PYTHON_FRAMEWORK=$(dirname $(dirname $(dirname $PYTHON_PATH)))/Python.framework
echo "Python framework path: $PYTHON_FRAMEWORK"

# 애플리케이션 빌드
python setup.py py2app

# libffi 라이브러리 찾기
LIBFFI_PATH=$(find /usr/local/Cellar /opt/homebrew/Cellar -name 'libffi*.dylib' | head -1)

# 프레임워크 디렉토리에 복사
if [ -n "$LIBFFI_PATH" ]; then
    echo "Copying $LIBFFI_PATH to app bundle..."
    mkdir -p dist/macOS\ Installer\ Downloader.app/Contents/Frameworks/
    cp $LIBFFI_PATH dist/macOS\ Installer\ Downloader.app/Contents/Frameworks/
    echo "Done!"
else
    echo "libffi library not found!"
fi

# Info.plist 수정
PLIST_PATH="dist/macOS Installer Downloader.app/Contents/Info.plist"
if [ -f "$PLIST_PATH" ]; then
    echo "Updating Info.plist..."
    # Python 런타임 위치 추가
    /usr/libexec/PlistBuddy -c "Add :PyRuntimeLocations array" "$PLIST_PATH" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :PyRuntimeLocations:0 string $PYTHON_FRAMEWORK/Versions/Current/Python" "$PLIST_PATH"
    echo "Info.plist updated!"
fi

echo "Build completed!" 
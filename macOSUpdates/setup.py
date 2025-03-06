"""
macOS 애플리케이션 빌드를 위한 설정 파일
Setup file for building macOS application
"""
from setuptools import setup
import os
import subprocess
import glob
import sys

# Python 프레임워크 경로 찾기
# Find Python framework path
def find_python_framework():
    python_path = sys.executable
    framework_path = os.path.normpath(os.path.join(os.path.dirname(python_path), '..', '..', 'Python.framework'))
    if os.path.exists(framework_path):
        return framework_path
    return None

# libffi 라이브러리 경로 찾기
# Find libffi library path
def find_libffi():
    try:
        # Homebrew나 시스템에 설치된 libffi 찾기
        # Find libffi installed via Homebrew or system
        cmd = "find /usr/local/Cellar /opt/homebrew/Cellar /usr/local/lib /opt/homebrew/lib -name 'libffi*.dylib' 2>/dev/null || true"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        paths = result.split('\n')
        if paths and paths[0]:
            return paths
    except:
        pass
    return []

# libffi 라이브러리 찾기
# Find libffi library
libffi_paths = find_libffi()

# Python 프레임워크 찾기
# Find Python framework
python_framework = find_python_framework()

# 프레임워크 파일 목록 생성
# Create list of framework files
frameworks = []
if libffi_paths:
    for path in libffi_paths:
        if os.path.exists(path):
            frameworks.append((path, os.path.join('Frameworks', os.path.basename(path))))

if python_framework:
    frameworks.append((python_framework, 'Python.framework'))

APP = ['macOSUpdate.py']
DATA_FILES = frameworks
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt5', 'datetime', 're', 'subprocess', 'os'],
    # 'iconfile': 'app_icon.icns',  # 주석 처리 또는 제거
    'plist': {
        'CFBundleName': 'macOS Installer Downloader',
        'CFBundleDisplayName': 'macOS Installer Downloader',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
        'CFBundleIdentifier': 'com.yourdomain.macosinstaller',  # 고유 식별자 설정
        'PyRuntimeLocations': [python_framework + '/Versions/Current/Python'] if python_framework else [],
    },
    'arch': 'universal2',  # Universal Binary 설정 (Intel + Apple Silicon)
    'includes': ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    'frameworks': libffi_paths + ([python_framework] if python_framework else []),
}

setup(
    name='macOS Installer Downloader',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 
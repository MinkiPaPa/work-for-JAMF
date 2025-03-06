import sys
import subprocess
import re
import os
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QProgressBar, 
                            QVBoxLayout, QWidget, QTextEdit, QLabel, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import logging
import tempfile

# 애플리케이션 리소스 경로 확인 함수
# Function to determine application resource path
def get_resource_path():
    """
    애플리케이션이 번들로 실행 중인지 확인하고 적절한 경로 반환
    Check if application is running as a bundle and return appropriate path
    """
    if getattr(sys, 'frozen', False):
        # 번들로 실행 중인 경우
        # If running as a bundle
        bundle_dir = os.path.dirname(sys.executable)
        # macOS 앱 번들 구조에 맞게 경로 조정
        # Adjust path according to macOS app bundle structure
        if os.path.basename(os.path.dirname(os.path.dirname(bundle_dir))) == 'Contents':
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(bundle_dir))))
        return bundle_dir
    # 스크립트로 실행 중인 경우
    # If running as a script
    return os.path.dirname(os.path.abspath(__file__))

# 임시 파일 경로 처리를 위한 함수
# Function to handle temporary file paths
def get_temp_path():
    """
    임시 파일 경로를 반환하는 함수 (/tmp 경로 사용)
    Returns temp file path using /tmp directory
    """
    # /tmp 디렉토리 내에 로그 디렉토리 생성
    # Create log directory in /tmp
    temp_dir = os.path.join('/tmp', 'macOSUpdatelog')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    return temp_dir

# 로그 파일 처리를 위한 함수
# Function to handle log files
def setup_logging():
    """
    로깅 설정을 초기화하는 함수
    Initialize logging configuration
    """
    log_dir = get_temp_path()
    log_file = os.path.join(log_dir, 'macOS_update.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

# 디버깅 정보 출력 함수
# Function to print debugging information
def debug_info():
    """
    디버깅 정보를 출력하는 함수
    Print debugging information
    """
    logging.debug(f"현재 작업 디렉토리 (Current working directory): {os.getcwd()}")
    logging.debug(f"시스템 경로 (System path): {sys.path}")
    logging.debug(f"환경 변수 (Environment variables): {dict(os.environ)}")
    
    if getattr(sys, 'frozen', False):
        logging.debug(f"PyInstaller 환경에서 실행 중 (Running in PyInstaller environment)")
        logging.debug(f"MEIPASS: {sys._MEIPASS}")

# 다운로드 작업을 위한 스레드 클래스
# Thread class for download operations
class DownloadThread(QThread):
    """
    다운로드 작업을 위한 스레드 클래스
    Download thread class for background processing
    """
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, log_file_path):
        """
        초기화 함수
        Initialization function
        """
        super().__init__()
        self.log_file_path = log_file_path

    def log_message(self, message):
        """
        로그 메시지를 파일에 기록하는 함수
        Function to record log messages to file
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 로그 파일에 메시지 추가
        # Add message to log file
        with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry)
        
        # UI에 상태 업데이트
        # Update status to UI
        self.status_signal.emit(message)

    def run(self):
        """
        스레드 실행 함수 - macOS 설치 프로그램 다운로드 수행
        Thread execution function - performs macOS installer download
        """
        try:
            self.log_message("다운로드 시작 (Download started)")
            
            # softwareupdate 명령어 실행
            # Execute softwareupdate command
            command = ['softwareupdate', '--fetch-full-installer', '--full-installer-version', '15.3.1']
            
            # 프로세스 실행
            # Execute process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # 진행률 추출을 위한 정규식 패턴
            # Regular expression pattern for progress extraction
            progress_pattern = r"(\d+\.?\d*)%"
            last_progress = 0

            # 프로세스 출력 실시간 처리
            # Real-time process output handling
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output = output.strip()
                    self.log_message(output)
                    
                    # 진행률 추출 및 시그널 발생
                    # Extract progress and emit signal
                    if "%" in output:
                        match = re.search(progress_pattern, output)
                        if match:
                            progress = int(float(match.group(1)))
                            if progress != last_progress:
                                self.progress_signal.emit(progress)
                                last_progress = progress
                                self.status_signal.emit(f"다운로드 진행 중: {progress}% (Downloading: {progress}%)")
                    
                    # 다운로드 상태 메시지 확인
                    # Check download status message
                    elif "Downloading" in output:
                        self.status_signal.emit("다운로드 시작... (Starting download...)")
                    elif "Verifying" in output:
                        self.status_signal.emit("다운로드 검증 중... (Verifying download...)")
                    elif "Installing" in output:
                        self.status_signal.emit("설치 중... (Installing...)")

            # 프로세스 종료 상태 확인
            # Check process exit status
            if process.returncode == 0:
                self.log_message("다운로드 완료 (Download completed)")
                self.progress_signal.emit(100)
                self.finished_signal.emit()
            else:
                error_msg = f"다운로드 중 오류가 발생했습니다. 종료 코드: {process.returncode}"
                self.log_message(error_msg)
                self.error_signal.emit(error_msg)

        except Exception as e:
            error_msg = f"예외 발생: {str(e)}"
            self.log_message(error_msg)
            self.error_signal.emit(error_msg)

# 메인 윈도우 클래스
# Main window class
class MainWindow(QMainWindow):
    """
    메인 윈도우 클래스
    Main window class
    """
    def __init__(self):
        """
        메인 윈도우 초기화 함수
        Main window initialization function
        """
        super().__init__()
        
        # 로그 디렉토리 설정
        # Set up log directory
        self.log_dir = get_temp_path()
        
        # 로그 파일 경로 설정
        # Set up log file path
        self.log_file_path = os.path.join(
            self.log_dir, 
            f"macOS_update_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        # UI 초기화 및 다운로드 스레드 준비
        # Initialize UI and prepare download thread
        self.initUI()
        self.download_thread = None

    def initUI(self):
        """
        UI 초기화 함수
        UI initialization function
        """
        # 윈도우 제목 및 크기 설정
        # Set window title and size
        self.setWindowTitle('macOS Installer Downloader')
        self.setGeometry(100, 100, 600, 400)

        # 중앙 위젯 설정
        # Set central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 다운로드 버튼 생성
        # Create download button
        self.download_button = QPushButton('macOS 15.3.1 다운로드', self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # 상태 레이블 추가
        # Add status label
        self.status_label = QLabel('준비됨 (Ready)', self)
        layout.addWidget(self.status_label)

        # 프로그레스 바 생성
        # Create progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # 로그 표시 영역 추가
        # Add log display area
        log_layout = QHBoxLayout()
        
        # 로그 레이블 추가
        # Add log label
        log_label = QLabel('로그 (Logs):', self)
        log_layout.addWidget(log_label)
        
        # 로그 파일 경로 표시
        # Display log file path
        log_path_label = QLabel(self)
        log_path_label.setText(f'로그 파일: {self.log_file_path}')
        log_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        log_layout.addWidget(log_path_label, stretch=1)
        
        layout.addLayout(log_layout)
        
        # 로그 텍스트 영역 추가
        # Add log text area
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def start_download(self):
        """
        다운로드 시작 함수
        Download start function
        """
        # 다운로드 버튼 비활성화 및 UI 초기화
        # Disable download button and initialize UI
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.status_label.setText('다운로드 준비 중... (Preparing download...)')
        
        # 로그 시작 메시지 추가
        # Add log start message
        start_message = f"=== macOS 15.3.1 다운로드 세션 시작 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==="
        with open(self.log_file_path, 'w', encoding='utf-8') as log_file:
            log_file.write(start_message + "\n")
        self.log_text.append(start_message)
        
        # 다운로드 스레드 생성 및 시작
        # Create and start download thread
        self.download_thread = DownloadThread(self.log_file_path)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.download_error)
        self.download_thread.start()

    def update_progress(self, value):
        """
        프로그레스 바 업데이트 함수
        Progress bar update function
        """
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """
        상태 메시지 업데이트 함수
        Status message update function
        """
        self.status_label.setText(message)
        self.log_text.append(message)
        # 항상 최신 로그가 보이도록 스크롤
        # Scroll to show the latest log
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def download_finished(self):
        """
        다운로드 완료 처리 함수
        Download completion handler function
        """
        # 다운로드 완료 후 UI 업데이트
        # Update UI after download completion
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText('다운로드 완료! (Download completed!)')
        
        # 완료 메시지 추가
        # Add completion message
        completion_message = f"=== 다운로드 완료 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==="
        self.log_text.append(completion_message)
        with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(completion_message + "\n")

    def download_error(self, error_message):
        """
        다운로드 에러 처리 함수
        Download error handler function
        """
        # 오류 발생 시 UI 업데이트
        # Update UI when error occurs
        self.download_button.setEnabled(True)
        self.status_label.setText(f'오류: {error_message} (Error: {error_message})')
        
        # 에러 메시지 추가
        # Add error message
        error_log = f"!!! 오류 발생: {error_message} !!!"
        self.log_text.append(error_log)
        with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(error_log + "\n")

# 메인 함수
# Main function
def main():
    """
    메인 함수 - 애플리케이션 실행
    Main function - run application
    """
    try:
        # QApplication 인스턴스 생성
        # Create QApplication instance
        app = QApplication(sys.argv)
        
        # 애플리케이션 아이콘 설정 시도
        # Try to set application icon
        try:
            app_path = get_resource_path()
            icon_path = os.path.join(app_path, "app_icon.icns")
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"아이콘 설정 중 오류 발생: {e}")
        
        # 메인 윈도우 생성 및 표시
        # Create and show main window
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        # 예외 처리 및 로깅
        # Exception handling and logging
        import traceback
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        print(traceback.format_exc())
        # 오류 메시지를 파일에 기록
        # Record error message to file
        with open(os.path.expanduser("~/Desktop/app_error.log"), "w") as f:
            f.write(f"오류: {e}\n")
            f.write(traceback.format_exc())

# 프로그램 진입점
# Program entry point
if __name__ == '__main__':
    main()
import os
from pathlib import Path

# Constants
BASE_FOLDER = 'chat-app'
SERVER_DOMAIN = ' supplychain.sentinel-cyber.sg'
USERNAME = 'admin'
PASSWORD = 'password123'
UPDATE_TIMEOUT = 3

# File contents
main_py = """import sys
from PyQt5.QtWidgets import QApplication
from chat_window import ChatWindow

def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    window.center()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
"""

update_service_py = """import paramiko
import socket
import os
from pathlib import Path

# Constants
SERVER_DOMAIN = 'supplychain.sentinel-cyber.sg'
USERNAME = 'admin'
PASSWORD = 'password123'
UPDATE_TIMEOUT = 3

def get_remote_file_path():
    if os.name == 'nt':  # Windows
        return '/tmp/updates/chatapp_1.2.exe'
    else:  # macOS or Linux
        return '/tmp/updates/chatapp_1.2'

def get_local_file_path():
    if os.name == 'nt':  # Windows
        local_dir = Path("C:/temp")
    else:  # macOS or Linux
        local_dir = Path.home() / "temp"
    
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir / "chatapp_1.2.exe"

def check_for_updates(status_callback):
    remote_file_path = get_remote_file_path()
    local_file_path = get_local_file_path()
    transport = None
    sftp = None

    try:
        status_callback("Connecting to update server...")
        
        # Use a socket to establish a connection with a timeout
        sock = socket.create_connection((SERVER_DOMAIN, 22), timeout=UPDATE_TIMEOUT)
        transport = paramiko.Transport(sock)
        
        transport.start_client(timeout=UPDATE_TIMEOUT)
        transport.auth_password(username=USERNAME, password=PASSWORD)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.get_channel().settimeout(UPDATE_TIMEOUT)
        
        status_callback("Downloading update...")
        sftp.get(remote_file_path, str(local_file_path))
        status_callback("Update downloaded successfully")

        return str(local_file_path)
    except (socket.timeout, paramiko.SSHException, paramiko.AuthenticationException) as e:
        status_callback("Failed to check for updates: {}".format(e))
        return None
    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()
"""

chat_window_py = """import os
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QMessageBox, QDialog, QLabel, QProgressBar
from PyQt5.QtCore import QTimer, Qt
from update_service import check_for_updates
from send_message_service import send_message

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(50)
        layout.addWidget(self.message_input)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.handle_send_message)
        layout.addWidget(send_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.check_for_updates()

    def handle_send_message(self):
        message = self.message_input.toPlainText().strip()
        if message:
            send_message(message, self.chat_display)
            self.message_input.clear()

    def check_for_updates(self):
        self.update_dialog = UpdateDialog(self)
        self.update_dialog.show()
        self.update_dialog.center()
        QTimer.singleShot(100, self._check_for_updates)

    def _check_for_updates(self):
        local_file_path = check_for_updates(self.update_dialog.update_status)
        if local_file_path:
            self.execute_update(local_file_path)
        else:
            self.update_dialog.close()

    def execute_update(self, file_path):
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to execute update: {e}")

    def center(self):
        frame_geom = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Checking for Updates")
        self.setGeometry(150, 150, 300, 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()

        self.label = QLabel("Checking for updates...")
        self.layout.addWidget(self.label)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)
        self.layout.addWidget(self.progress)

        self.setLayout(self.layout)
        self.center()

    def update_status(self, message):
        self.label.setText(message)
        if "successfully" in message or "Failed" in message:
            self.progress.setRange(0, 1)
            QTimer.singleShot(3000, self.close)

    def center(self):
        frame_geom = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())
"""

send_message_service_py = """def send_message(message, chat_display):
    chat_display.append(f"You: {message}")
"""

requirements_txt = """PyQt5
paramiko
"""

readme_md = """# Chat Application

Welcome to our open-source Chat Application! 🎉

## Overview

This chat application is a simple yet functional platform for real-time communication. Built with PyQt5 and Python, it showcases basic functionalities of a chat service, making it a great starting point for anyone looking to learn about desktop application development.

## Features

- **Real-Time Messaging:** Send and receive messages instantly.
- **User-Friendly Interface:** Simple and intuitive design inspired by popular chat applications.
- **Open Source:** Freely available for modification and enhancement.

## How to Use

### Setup

1. **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd chat-app
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application:**

    ```bash
    python main.py
    ```

### Code Structure

- **main.py:** Entry point of the application.
- **chat_window.py:** Contains the main chat window logic.
- **send_message_service.py:** Handles sending messages.
- **update_service.py:** Checks for updates from the server.
- **requirements.txt:** Lists the dependencies for the project.

## Contributing

We welcome contributions from the community! Feel free to fork the repository and submit pull requests.

## License

This project is licensed under the MIT License.

Happy chatting! 💬
"""

build_sh = """#!/bin/bash
pyinstaller --name=chatapp --onefile --windowed main.py
"""

build_bat = """@echo off
pyinstaller --name=chatapp --onefile --windowed main.py
"""

# Create the directory structure
def create_file_tree():
    os.makedirs(BASE_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(BASE_FOLDER, 'resources'), exist_ok=True)

    # Write files
    with open(os.path.join(BASE_FOLDER, 'main.py'), 'w') as f:
        f.write(main_py)

    with open(os.path.join(BASE_FOLDER, 'update_service.py'), 'w') as f:
        f.write(update_service_py)

    with open(os.path.join(BASE_FOLDER, 'chat_window.py'), 'w') as f:
        f.write(chat_window_py)

    with open(os.path.join(BASE_FOLDER, 'send_message_service.py'), 'w') as f:
        f.write(send_message_service_py)

    with open(os.path.join(BASE_FOLDER, 'requirements.txt'), 'w') as f:
        f.write(requirements_txt)

    with open(os.path.join(BASE_FOLDER, 'README.md'), 'w') as f:
        f.write(readme_md)

    with open(os.path.join(BASE_FOLDER, 'build.sh'), 'w') as f:
        f.write(build_sh)
    
    with open(os.path.join(BASE_FOLDER, 'build.bat'), 'w') as f:
        f.write(build_bat)

    # Make build.sh executable
    os.chmod(os.path.join(BASE_FOLDER, 'build.sh'), 0o755)

if __name__ == "__main__":
    create_file_tree()
    print(f"File tree created in {BASE_FOLDER}")
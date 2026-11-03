import os
import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QMessageBox, QDialog, QLabel, QProgressBar
from PyQt5.QtCore import QTimer, Qt
from update_service import get_local_file_path, check_for_updates
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

        QTimer.singleShot(900, self.check_for_updates)

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
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-n", file_path])
            elif os.name == "nt":
                os.startfile(file_path)
            else:
                subprocess.Popen([file_path])

            QTimer.singleShot(2000, self.exit_app)

        except (OSError, subprocess.SubprocessError) as e:
            self.update_error = e
            QTimer.singleShot(3000, self.failed_to_update_message)
    
    def failed_to_update_message(self):
        QMessageBox.critical(self, "Update Error", f"Failed to execute update: {self.update_error}")

    def exit_app(self):
        QApplication.quit()

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

        if get_local_file_path().is_file():
            QTimer.singleShot(900, self.up_to_date_message)
        
        self.setLayout(self.layout)
        self.center()

    def update_status(self, message):
        self.label.setText(message)
        if "successfully" in message or "Failed" in message:
            self.progress.setRange(0, 1)
            QTimer.singleShot(3000, self.close)

    def up_to_date_message(self):
        QMessageBox.information(self, "Update Check", "Already up to date")
        self.close()

    def center(self):
        frame_geom = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

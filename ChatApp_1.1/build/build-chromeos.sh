#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p  "$HOME/.venvs"
python3 -m venv "$HOME/.venvs/chatapp_1.1"
source "$HOME/.venvs/chatapp_1.1/bin/activate"
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --onefile --add-data "update_service.py:." --windowed --name="chatapp_1.1" main.py

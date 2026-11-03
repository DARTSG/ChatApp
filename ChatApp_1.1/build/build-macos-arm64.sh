#!/bin/bash
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --windowed --name="chatapp_1.1" main.py

@echo off
echo Building TokenHub...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --onedir --noconsole --name TokenHub --clean src/main.py
echo Build complete. Check dist\TokenHub\
pause
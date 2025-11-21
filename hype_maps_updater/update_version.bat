@echo off
SETLOCAL
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_version.ps1"
ENDLOCAL

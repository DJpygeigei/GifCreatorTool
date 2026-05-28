@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 查找 Python
set PYTHON=
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        goto :run
    )
)
python --version >nul 2>&1
if not errorlevel 1 set PYTHON=python

:run
if "%PYTHON%"=="" (
    echo 未找到 Python！请安装 Python 3.10+ 并确保已勾选 "Add to PATH"
    pause
    exit /b 1
)

echo 使用: %PYTHON%
%PYTHON% -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo 安装依赖中...
    %PYTHON% -m pip install PySide6 -q
)

%PYTHON% main.py
if errorlevel 1 pause

@echo off
chcp 65001 >nul
echo ============================================
echo   GIF Tool - 一键安装 + 打包
echo ============================================
echo.

:: ── 查找 Python ──────────────────────────────
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
        goto :found_python
    )
)

:: 尝试系统 PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :found_python
)

echo 错误: 未找到 Python！
echo 请从 https://www.python.org/downloads/ 安装 Python 3.10+
echo 安装时勾选 "Add Python to PATH"
pause
exit /b 1

:found_python
echo 找到 Python: %PYTHON%
%PYTHON% --version
echo.

:: ── 安装依赖 ──────────────────────────────────
echo [1/3] 安装 Python 依赖 (PySide6 + PyInstaller)...
%PYTHON% -m pip install PySide6 pyinstaller --upgrade -q
if errorlevel 1 (
    echo 错误: 安装依赖失败
    pause
    exit /b 1
)
echo 依赖安装完成。
echo.

:: ── 检查 ffmpeg ───────────────────────────────
echo [2/3] 检查 ffmpeg...
if exist "ffmpeg.exe" (
    echo 找到 ffmpeg.exe ✓
) else (
    echo.
    echo [警告] 未找到 ffmpeg.exe！
    echo.
    echo 请按以下步骤下载 ffmpeg：
    echo 1. 访问 https://www.gyan.dev/ffmpeg/builds/
    echo 2. 下载 "ffmpeg-release-essentials.zip"
    echo 3. 解压后将 bin\ 目录中的 ffmpeg.exe 和 ffprobe.exe
    echo    复制到本文件夹（%~dp0）
    echo 4. 重新运行此脚本
    echo.
    echo 如果 ffmpeg 已在系统 PATH，运行时也可正常工作（但打包的exe不含ffmpeg）
    echo.
    choice /C YN /M "是否继续打包（ffmpeg不会内嵌到exe中）？"
    if errorlevel 2 goto :end
)
echo.

:: ── 生成 spec（不嵌入ffmpeg，由外部提供）──────
echo [3/3] 打包为 exe...

:: 根据是否存在 ffmpeg.exe 选择打包方式
if exist "ffmpeg.exe" (
    echo 检测到 ffmpeg.exe，将内嵌到 exe...
    %PYTHON% -m PyInstaller giftool.spec --noconfirm
) else (
    echo ffmpeg 不内嵌，生成不含 ffmpeg 的 exe...
    %PYTHON% -m PyInstaller ^
        --onefile ^
        --windowed ^
        --name GIFTool ^
        --hidden-import PySide6.QtMultimedia ^
        --hidden-import PySide6.QtMultimediaWidgets ^
        --noconfirm ^
        main.py
)

if errorlevel 1 (
    echo.
    echo 打包失败！查看上方错误信息。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成！
echo   exe 位置: %~dp0dist\GIFTool.exe
echo ============================================
:end
pause

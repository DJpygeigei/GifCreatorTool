# GIF Tool - PyInstaller spec file
# 运行: pyinstaller giftool.spec
import os
import sys

# 收集存在的 PNG 图标文件（1-17）
_png_files = [(f'{i}.png', '.') for i in range(1, 18)
              if os.path.exists(f'{i}.png')]

# 打包说明文档（docs/ 目录）
import glob as _glob
_doc_files = []
for _f in _glob.glob('docs/**/*', recursive=True):
    if os.path.isfile(_f):
        _rel_dir = os.path.dirname(_f)
        _doc_files.append((_f, _rel_dir))

# 跨平台 ffmpeg 二进制
if sys.platform == 'win32':
    _bins = [('ffmpeg.exe', '.'), ('ffprobe.exe', '.')]
    _icon = 'logo.ico'
else:
    _bins = []
    for _name in ('ffmpeg', 'ffprobe'):
        if os.path.exists(_name):
            _bins.append((_name, '.'))
    _icon = 'logo.icns' if os.path.exists('logo.icns') else None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=_bins,
    datas=_png_files + _doc_files,
    hiddenimports=[
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GIFTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
    uac_admin=False,
    version=None,
)

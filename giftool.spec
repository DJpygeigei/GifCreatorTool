# GIF Tool - PyInstaller spec file
# 运行: pyinstaller giftool.spec
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

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

# 完整收集 mss / Pillow / numpy（含数据文件和二进制）
_extra_datas, _extra_bins, _extra_hidden = [], [], []
for _pkg in ('mss', 'PIL', 'numpy'):
    try:
        d, b, h = collect_all(_pkg)
        _extra_datas  += d
        _extra_bins   += b
        _extra_hidden += h
    except Exception:
        pass

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=_bins + _extra_bins,
    datas=_png_files + _doc_files + _extra_datas,
    hiddenimports=[
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'mss',
        'mss.windows',
        'mss.darwin',
        'mss.linux',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'numpy',
    ] + _extra_hidden,
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

# macOS：打成 .app bundle，双击不会弹 Terminal
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='GIFTool.app',
        icon=_icon,
        bundle_identifier='com.wupengyu1.giftool',
        info_plist={
            'CFBundleDisplayName': 'GIFTool',
            'CFBundleShortVersionString': '1.0.5',
            'NSHighResolutionCapable': True,
            # 隐藏 Dock 以外的终端窗口
            'LSUIElement': False,
            # 屏幕录制权限说明
            'NSScreenCaptureDescription':
                'GIFTool 需要屏幕录制权限以录制 GIF',
        },
    )

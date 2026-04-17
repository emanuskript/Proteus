# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Proteus (PySide6 version).

Usage:
    pyinstaller --clean --noconfirm packaging/Proteus.spec

Icons (place these files in packaging/ before building):
    Windows : packaging/Proteus.ico   (256x256 multi-size ICO)
    macOS   : packaging/Proteus.icns  (converted from 1024x1024 PNG via iconutil)
    Linux   : no icon needed; the .png is embedded as app_datas
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# ---- Project root (one level up from packaging/) ----
PROJECT_ROOT = os.path.normpath(os.path.join(SPECPATH, '..'))

# ---- Version (single source of truth: pyproject.toml) ----
APP_VERSION = "3.0.1"
APP_NAME    = 'Proteus'

# ---- Configuration ----
ONEFILE = False

# ---- Platform-aware icon ----
_ico  = os.path.join(SPECPATH, 'Proteus.ico')
_icns = os.path.join(SPECPATH, 'Proteus.icns')

if sys.platform == 'win32' and os.path.isfile(_ico):
    ICON = _ico
elif sys.platform == 'darwin' and os.path.isfile(_icns):
    ICON = _icns
else:
    ICON = None          # Linux: no icon needed in EXE

# ---- PySide6 data files ----
# Only collect plugins needed for basic widget rendering (platforms, imageformats, styles).
pyside6_datas = collect_data_files('PySide6', includes=[
    'plugins/platforms/**',
    'plugins/imageformats/**',
    'plugins/styles/**',
    'plugins/xcbglintegrations/**',
    'plugins/platforminputcontexts/**',
    'plugins/egldeviceintegrations/**',
])

# ---- Hidden imports ----
# Only the 3 PySide6 modules Proteus actually uses (not all 40+).
all_hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

# ---- Application data files ----
app_datas = [
    (os.path.join(PROJECT_ROOT, 'src', 'proteus', 'resources', 'Proteus.png'),
     os.path.join('proteus', 'resources')),
]

all_datas = app_datas + pyside6_datas

# ---- Excludes ----
# Unused Qt modules that PyInstaller may pull in transitively.
_unused_qt = [
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
    'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtConcurrent',
    'PySide6.QtDataVisualization', 'PySide6.QtDBus', 'PySide6.QtDesigner',
    'PySide6.QtHelp', 'PySide6.QtHttpServer',
    'PySide6.QtLocation', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetworkAuth', 'PySide6.QtNfc',
    'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
    'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtPositioning',
    'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuick3D',
    'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSensors',
    'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
    'PySide6.QtSpatialAudio', 'PySide6.QtSql', 'PySide6.QtStateMachine',
    'PySide6.QtSvg', 'PySide6.QtSvgWidgets', 'PySide6.QtTest',
    'PySide6.QtTextToSpeech', 'PySide6.QtUiTools',
    'PySide6.QtWebChannel', 'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebSockets', 'PySide6.QtXml',
]

excludes = [
    # Unused Python packages
    'matplotlib', 'scipy', 'pandas', 'pytest', 'IPython',
    'notebook', 'sphinx', 'tkinter', 'customtkinter',
    'PIL', 'Pillow', 'PyQt5', 'PyQt6', 'wx',
] + _unused_qt

# ---- Analysis ----
a = Analysis(
    [os.path.join(PROJECT_ROOT, 'src', 'proteus', 'app.py')],
    pathex=[os.path.join(PROJECT_ROOT, 'src')],
    binaries=[],
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ---- Windows version metadata ----
_version_file = os.path.join(SPECPATH, 'version_info.txt')
_win_version   = _version_file if sys.platform == 'win32' and os.path.isfile(_version_file) else None

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
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
        icon=ICON,
        version=_win_version,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON,
        version=_win_version,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

# ---- macOS .app bundle ----
if sys.platform == 'darwin':
    app = BUNDLE(
        coll if not ONEFILE else exe,
        name=f'{APP_NAME}.app',
        icon=ICON,
        bundle_identifier='com.proteus.image',
        info_plist={
            'CFBundleName':              APP_NAME,
            'CFBundleDisplayName':       APP_NAME,
            'CFBundleVersion':           APP_VERSION,
            'CFBundleShortVersionString': APP_VERSION,
            'NSHighResolutionCapable':   True,
            'LSMinimumSystemVersion':    '11.0',
            'NSHumanReadableCopyright':  f'Copyright 2024 Proteus. All rights reserved.',
        },
    )

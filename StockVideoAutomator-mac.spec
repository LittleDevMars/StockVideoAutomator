# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None
ROOT = os.path.abspath(os.path.dirname(SPECPATH))

a = Analysis(
    ['main.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('app/resources/style.qss', 'app/resources'),
        ('app/resources/app_icon.ico', 'app/resources'),
        ('app/resources/app_icon.png', 'app/resources'),
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtNetwork',
        'requests',
        'sqlite3',
        'app.bridge',
        'app.bridge.bridge_server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter',
        'unittest', 'test',
        'pydoc', 'doctest',
        'lib2to3',
        'numpy', 'pandas', 'matplotlib', 'scipy',
        'PIL', 'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockVideoAutomator',
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
    icon='app/resources/app_icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='StockVideoAutomator',
)

app = BUNDLE(
    coll,
    name='StockVideoAutomator.app',
    icon='app/resources/app_icon.png',
    bundle_identifier='com.stockvideoautomator.app',
)

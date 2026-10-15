# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import sys

block_cipher = None

project_dir = os.path.abspath(SPECPATH)

# CustomTkinter asset detection
import customtkinter
ctk_dir = os.path.dirname(customtkinter.__file__)

datas = [
    (os.path.join(project_dir, 'assets'), 'assets'),
    (ctk_dir, 'customtkinter'),
]

hiddenimports = [
    'customtkinter',
    'watchdog',
    'watchdog.observers',
    'watchdog.observers.winapi',
    'pystray',
    'PIL',
    'PIL.ImageTk',
    'send2trash',
    'psutil',
    'sqlite3',
    'ctypes',
    'win32api',
    'win32con',
    'win32gui',
]

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'pytest'],
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
    name='OpenSearch',
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
    icon=os.path.join(project_dir, 'assets', 'icons', 'opensearch.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenSearch',
)

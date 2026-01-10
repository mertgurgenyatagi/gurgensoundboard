# -*- mode: python ; coding: utf-8 -*-
import os

spec_root = os.path.abspath(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'webview',
        'pystray',
        'PIL',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'winsound',
        'wave',
        'json',
        'base64',
        'threading',
        'keyboard',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='gurgensoundboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(spec_root, 'assets', 'images', 'app_logo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='gurgensoundboard',
)

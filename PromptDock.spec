# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["prompt_dock.py"],
    pathex=[],
    binaries=[],
    datas=[("icon.ico", "."), ("icon_src.png", "."), ("icon_taskbar.png", ".")],
    hiddenimports=["Crypto", "Crypto.Cipher.AES", "Crypto.Util.Padding", "requests", "urllib3", "charset_normalizer", "schedule_pad"],
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
    a.binaries,
    a.datas,
    [],
    name="PromptDock",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["icon.ico"],
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/data/workspace/job-hunt/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/data/workspace/job-hunt/ui/static', 'ui/static')],
    hiddenimports=['openpyxl', 'pandas', 'requests', 'bs4', 'webview', 'curl_cffi', 'jobspy'],
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
    name='JobHunterGermany',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JobHunterGermany',
)

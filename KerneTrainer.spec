# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['k:\\kerne mid feb\\neural net\\gui_trainer.py'],
    pathex=[],
    binaries=[],
    datas=[('k:\\kerne mid feb\\neural net\\src', 'src')],
    hiddenimports=['matplotlib.backends.backend_tkagg', 'torch', 'numpy', 'pandas', 'requests', 'tqdm'],
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
    name='KerneTrainer',
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
    name='KerneTrainer',
)

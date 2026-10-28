# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = [('build/pkg/builds.json', '.'), ('lang', 'lang'), ('meta', 'meta'), ('icon', 'icon'), ('art', 'art')]
binaries = []
hiddenimports = ['PIL._tkinter_finder', 'PIL.ImageTk', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'ocr_backend', 'features', 'stash', 'vendor', 'companion', 'share', 'dropstats', 'updater', 'syncer', 'gameinfo', 'updates', 'reports', 'account', 'service', 'screenstate', 'localapi', 'presence', 'notify', 'knowledge', 'voicepack', 'livetranslate', 'single', 'tasks_live', 'overlay', 'terms', 'trscreen', 'speech', 'winocr', 'gamepad', 'safeio', 'winpath', 'pystray._win32', 'fx', 'bgvideo', 'view3d', 'display']
datas += copy_metadata('edge-tts')
tmp_ret = collect_all('edge_tts')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('aiohttp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('av')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('tokenizers')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('huggingface_hub')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('rapidocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('onnxruntime')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ctranslate2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sentencepiece')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('soundcard')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('winrt')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TD2LootAdvisor',
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
    icon=['build/td2.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TD2LootAdvisor',
)

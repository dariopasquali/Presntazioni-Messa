# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

project_dir = Path(SPECPATH).resolve()
app_name = 'PresentazioniMessa'

# qt-material resolves themes, SVG resources and package metadata dynamically.
qt_material_datas, qt_material_binaries, qt_material_hiddenimports = collect_all('qt_material')

# gdown reads its installed version through importlib.metadata at runtime.
metadata_datas = []
for distribution in ('gdown', 'qt-material'):
    try:
        metadata_datas += copy_metadata(distribution)
    except Exception:
        # Keep the spec usable across environments where metadata layout differs.
        pass

# Runtime files used directly by the application. Keep writable/configurable files
# beside the executable because this is an onedir build.
project_datas = []
for filename in (
    'custom.css',
    'librone.json',
    'start.png',
    'sunday_image.jpg',
    'version.txt',
    'PresentazioniMessa.ico',
):
    source = project_dir / filename
    if source.is_file():
        project_datas.append((str(source), '.'))

# The application loads the Noto Sans files at runtime.
fonts_dir = project_dir / 'fonts'
if fonts_dir.is_dir():
    project_datas.append((str(fonts_dir), 'fonts'))

analysis = Analysis(
    [str(project_dir / 'launcher.py')],
    pathex=[str(project_dir)],
    binaries=qt_material_binaries,
    datas=qt_material_datas + metadata_datas + project_datas,
    hiddenimports=qt_material_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

# Use an onedir build. librone.json, version.txt, downloaded images and update
# artifacts are read or modified at runtime and must not live in a onefile temp dir.
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
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
    uac_admin=False,
    icon=str(project_dir / 'PresentazioniMessa.ico'),
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=app_name,
)

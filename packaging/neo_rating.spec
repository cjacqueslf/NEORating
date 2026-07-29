# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata


project_root = Path(SPECPATH).parent
scientific_data = project_root / "resources" / "scientific"

datas = [
    (str(scientific_data), "resources/scientific"),
    (str(project_root / "licenses"), "licenses"),
    (str(project_root / "README.md"), "."),
    (str(project_root / "THIRD_PARTY_NOTICES.md"), "."),
    (str(project_root / "UPDATE_POLICY.md"), "."),
]
datas += copy_metadata("digest2")

analysis = Analysis(
    [str(project_root / "src" / "neo_rating" / "presentation" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("digest2"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="NEORating",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

distribution = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NEORating-0.1.0-portable",
)

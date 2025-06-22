# -*- mode: python ; coding: utf-8 -*-
import sys
import sysconfig
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Get site-packages directory dynamically
site_packages = sysconfig.get_paths()["purelib"]

# Collect all submodules of pyproj and rasterio
hiddenimports_pyproj = collect_submodules('pyproj')
hiddenimports_rasterio = collect_submodules('rasterio')

a = Analysis(
    ['send.py'],
    pathex=[],
    binaries=[],
    datas=[
        (f'{site_packages}/pyproj/proj_dir/share/proj', 'pyproj/proj_dir/share/proj'),
        (f'{site_packages}/rasterio/gdal_data', 'gdal_data'),
        (f'{site_packages}/rasterio/proj_data', 'rasterio/proj_data')
    ],
    hiddenimports=['rasterio.sample', 'rasterio.vrt', 'rasterio._features', 'fiona', 'pyogrio'] + hiddenimports_rasterio + hiddenimports_pyproj,
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
    name='sender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='build_attributes\\version.txt',  # <-- Add this line
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sender',
)

# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None


a = Analysis(['pitcrew/cli.py'],
             pathex=['pitcrew'],
             binaries=[],
             datas=collect_data_files("pitcrew.tasks", include_py_files=True),
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='crew',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

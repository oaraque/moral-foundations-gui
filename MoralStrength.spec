# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


import os
spec_root = os.path.abspath(SPECPATH)


a = Analysis(['gui.py'],
             pathex=[spec_root],
             binaries=[],
             datas= [ ('export/*.pck', 'export'),('moralstrength_annotations/*.tsv', 'moralstrength_annotations') ],
             hiddenimports=[ 'spacy', 'sklearn.neighbors.typedefs', 'srsly.msgpack.util','tkinter'],
             hookspath=[spec_root],
             runtime_hooks=['runtimehook-spacy.py'],
             excludes=['qt5','PyQT5',
				'bokeh','notebook',
				'botocore','bottleneck','gevent','gevent-1.4.0-py3.7.egg-info', 'llvmlite','tornado','python-qt',
				],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MoralStrength',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False , icon='icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='MoralStrength')

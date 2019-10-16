rmdir /q /s build
rmdir /q /s dist\MoralStrength
pyinstaller MoralStrength.spec

REM I can't understand why the exclude doesn't work, but we can remove stuff from here I guess...
rmdir /q /s dist\MoralStrength\PyQt5
del dist\MoralStrength\Qt5*.dll
rmdir /q /s dist\MoralStrength\share

REM Idem for upx... 
upx -9 dist\MoralStrength\mkl_core.dll | upx -9 dist\MoralStrength\lib*.dll | upx -9 dist\MoralStrength\mkl_v*.dll | upx -9 dist\MoralStrength\mkl_avx*.dll | upx -9 dist\MoralStrength\mkl_b*.dll
upx -9 dist\MoralStrength\mkl*.dll | upx -9 dist\icud*.dll | upx -9 dist\hdf5.dll

dist\MoralStrength\MoralStrength.exe
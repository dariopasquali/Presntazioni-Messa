@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "DIST_DIR=%CD%\dist\PresentazioniMessa"
set "APP_EXE=%DIST_DIR%\PresentazioniMessa.exe"

echo [1/4] Checking build dependencies...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is missing. Installing it in the active environment...
    python -m pip install --upgrade pyinstaller
    if errorlevel 1 goto error
)

echo [2/4] Building the PyInstaller distribution...
python -m PyInstaller --noconfirm --clean launcher.spec
if errorlevel 1 goto error

if not exist "%APP_EXE%" (
    echo ERROR: PyInstaller did not create:
    echo   %APP_EXE%
    goto error
)

echo [3/4] Copying runtime resources next to the executable...

if not exist "%CD%\custom.css" (
    echo ERROR: Required file not found: %CD%\custom.css
    goto error
)
copy /y "%CD%\custom.css" "%DIST_DIR%\custom.css" >nul
if errorlevel 1 goto copy_error

if not exist "%CD%\librone.json" (
    echo ERROR: Required file not found: %CD%\librone.json
    goto error
)
copy /y "%CD%\librone.json" "%DIST_DIR%\librone.json" >nul
if errorlevel 1 goto copy_error

if not exist "%CD%\start.png" (
    echo ERROR: Required file not found: %CD%\start.png
    goto error
)
copy /y "%CD%\start.png" "%DIST_DIR%\start.png" >nul
if errorlevel 1 goto copy_error

if not exist "%CD%\version.txt" (
    echo ERROR: Required file not found: %CD%\version.txt
    goto error
)
copy /y "%CD%\version.txt" "%DIST_DIR%\version.txt" >nul
if errorlevel 1 goto copy_error

if exist "%CD%\PresentazioniMessa.ico" (
    copy /y "%CD%\PresentazioniMessa.ico" "%DIST_DIR%\PresentazioniMessa.ico" >nul
    if errorlevel 1 goto copy_error
)

if not exist "%CD%\fonts\" (
    echo ERROR: Required directory not found: %CD%\fonts
    goto error
)
if exist "%DIST_DIR%\fonts\" rmdir /s /q "%DIST_DIR%\fonts"
xcopy "%CD%\fonts" "%DIST_DIR%\fonts\" /e /i /h /y >nul
if errorlevel 1 (
    echo ERROR: Could not copy the fonts directory.
    goto error
)

if exist "%CD%\sunday_image.jpg" (
    copy /y "%CD%\sunday_image.jpg" "%DIST_DIR%\sunday_image.jpg" >nul
    if errorlevel 1 goto copy_error
)

for %%F in (custom.css librone.json start.png version.txt) do (
    if not exist "%DIST_DIR%\%%F" (
        echo ERROR: Runtime file missing from distribution: %%F
        goto error
    )
)
if not exist "%DIST_DIR%\fonts\" (
    echo ERROR: Runtime directory missing from distribution: fonts
    goto error
)

echo [4/4] Building the Inno Setup installer...
where ISCC.exe >nul 2>&1
if not errorlevel 1 (
    ISCC.exe PresentazioniMessa.iss
    if errorlevel 1 goto error
    goto done
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    "%ISCC%" PresentazioniMessa.iss
    if errorlevel 1 goto error
    goto done
)

echo ERROR: ISCC.exe was not found.
echo Install Inno Setup 6, then run:
echo   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" PresentazioniMessa.iss
goto error

:copy_error
echo ERROR: A runtime resource could not be copied to:
echo   %DIST_DIR%
goto error

:error
echo.
echo Distribution build failed.
endlocal
exit /b 1

:done
echo.
echo Build complete.
echo Application: dist\PresentazioniMessa\PresentazioniMessa.exe
echo Installer:   installer\PresentazioniMessa-Setup-2.0.exe
endlocal
exit /b 0

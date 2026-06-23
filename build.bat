@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ===================================
echo  Media Converter - Release Build
echo ===================================
echo.

python --version > nul 2>&1
if errorlevel 1 ( echo [ERROR] Python not found. & pause & exit /b 1 )

git --version > nul 2>&1
if errorlevel 1 ( echo [ERROR] Git not found.  Install: https://git-scm.com/ & pause & exit /b 1 )
git config --global --add safe.directory "%CD:\=/%"

for /f "delims=" %%i in ('git config --global user.email 2^>nul') do set GIT_EMAIL=%%i
if "!GIT_EMAIL!"=="" (
    set /p GIT_EMAIL=Git email e.g. you@example.com:
    git config --global user.email "!GIT_EMAIL!"
)
for /f "delims=" %%i in ('git config --global user.name 2^>nul') do set GIT_NAME=%%i
if "!GIT_NAME!"=="" (
    set /p GIT_NAME=Git name e.g. Aki:
    git config --global user.name "!GIT_NAME!"
)

gh --version > nul 2>&1
if errorlevel 1 ( echo [ERROR] GitHub CLI not found.  Install: https://cli.github.com/ & pause & exit /b 1 )

gh auth status > nul 2>&1
if errorlevel 1 ( echo [ERROR] Not logged in.  Run: gh auth login & pause & exit /b 1 )

echo.
set /p VERSION=Version e.g. 1.2.0:
if "!VERSION!"=="" ( echo [ERROR] Version required. & pause & exit /b 1 )

git rev-parse --verify refs/tags/v!VERSION! > nul 2>&1
if not errorlevel 1 ( echo [ERROR] Tag v!VERSION! already exists. & pause & exit /b 1 )

echo ## v!VERSION! > CHANGES.txt
echo. >> CHANGES.txt
echo - >> CHANGES.txt
echo Write release notes in the Notepad window, then save and close.
start /wait notepad CHANGES.txt

for %%F in (CHANGES.txt) do if %%~zF==0 (
    echo [ERROR] Release notes cannot be empty.
    pause & exit /b 1
)

echo.
echo [0/4] Setting version !VERSION!...
python update_version.py !VERSION!
if errorlevel 1 ( echo [ERROR] Version update failed. & pause & exit /b 1 )
echo       Done

echo.
echo [1/4] Installing packages...
pip install pillow pillow-heif rawpy pyinstaller --upgrade --quiet
if errorlevel 1 ( echo [ERROR] Package install failed. & pause & exit /b 1 )
echo       Done

echo.
echo [2/4] Cleaning old build...
taskkill /f /im converter.exe > nul 2>&1
if exist build     rmdir /s /q build
if exist dist      rmdir /s /q dist
if exist installer rmdir /s /q installer
echo       Done

echo.
echo [3/4] Building with PyInstaller...
python -m PyInstaller converter.spec --noconfirm
if errorlevel 1 ( echo [ERROR] PyInstaller failed. & pause & exit /b 1 )
echo       Done

echo.
echo [4/4] Building installer...
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"      set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

set ASSET=dist\converter.exe
if "!ISCC!"=="" (
    echo [SKIP] Inno Setup not found.  Releasing dist\converter.exe instead.
) else (
    "!ISCC!" installer.iss
    if errorlevel 1 ( echo [ERROR] Inno Setup failed. & pause & exit /b 1 )
    set ASSET=installer\MediaConverter_Setup.exe
    echo       Done
)

:: ---- Git + GitHub ----

if not exist ".git" (
    git init
    git branch -M main
)

if not exist ".gitignore" (
    echo build/>.gitignore
    echo dist/>>.gitignore
    echo installer/>>.gitignore
    echo __pycache__/>>.gitignore
    echo *.pyc>>.gitignore
)

git add converter.py converter.spec version_info.txt installer.iss build.bat update_version.py logo.ico CHANGES.txt .gitignore README.md
git commit -m "Release v!VERSION!"
if errorlevel 1 ( echo [ERROR] Commit failed. & pause & exit /b 1 )

set PUSHED=0
git remote get-url origin > nul 2>&1
if errorlevel 1 (
    set /p REPO=GitHub repo name e.g. media-converter:
    gh repo create !REPO! --public --source=. --remote=origin --push
    if errorlevel 1 ( echo [ERROR] Failed to create GitHub repo. & pause & exit /b 1 )
    set PUSHED=1
)

if "!PUSHED!"=="0" (
    git push -u origin main
    if errorlevel 1 ( echo [ERROR] git push failed. & pause & exit /b 1 )
)

git tag v!VERSION!
git push origin v!VERSION!

echo.
echo [GitHub] Creating release v!VERSION!...
gh release create v!VERSION! "!ASSET!" --title "Media Converter v!VERSION!" --notes-file CHANGES.txt
if errorlevel 1 ( echo [ERROR] Release creation failed. & pause & exit /b 1 )

echo.
echo ===================================
echo  Release v!VERSION! is live!
echo ===================================
echo.

endlocal
pause

@echo off
chcp 65001 >nul
setlocal
set "VIDEO=%~dp0rick_edit.mp4"
if not "%~1"=="" set "VIDEO=%~1"

python -c "import imageio_ffmpeg, PIL" >nul 2>nul
if errorlevel 1 (
  echo Устанавливаю зависимости при первом запуске...
  python -m pip install -r "%~dp0requirements.txt"
  if errorlevel 1 (
    echo Не удалось установить зависимости. Проверь Python и подключение к интернету.
    pause
    exit /b 1
  )
)

python "%~dp0ascii_video.py" "%VIDEO%" --start 0 --color --fit stretch --zoom 1.7
pause

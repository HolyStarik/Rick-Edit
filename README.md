# Rick ASCII Edit

Проигрыватель для Windows CMD, Windows Terminal и Linux-терминала: показывает ролик в цветных ASCII-символах по центру, подстраивая размер под окно терминала. Первые четыре секунды исходника пропускаются автоматически, а ролик повторяется до остановки через `Ctrl+C`.

Видео `rick_edit.mp4` лежит рядом со скриптом. Остановка — `Ctrl+C`.

## Arch Linux

Установи Python и Git, если их ещё нет, затем склонируй репозиторий:

```bash
sudo pacman -S --needed git python python-pip
git clone https://github.com/HolyStarik/Rick-Edit.git
cd Rick-Edit
./run.sh
```

`run.sh` создаст локальное виртуальное окружение `.venv` и установит зависимости при первом запуске. В следующий раз достаточно выполнить `./run.sh`.

Для другого файла передай путь первым аргументом:

```bash
./run.sh "/путь/к/видео.mp4"
```

## Windows

Установи Python 3.10 или новее, клонируй репозиторий и запусти `run.cmd`. При первом запуске он установит нужные Python-библиотеки.

## Ручной запуск

На Linux сначала установи зависимости в виртуальное окружение:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ascii_video.py "rick_edit.mp4" --start 4 --color
```

Можно менять `--width` и `--fps`, чтобы подстроить размер и плавность под экран.

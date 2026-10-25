# Rick ASCII Edit

Проигрыватель для Windows CMD / Windows Terminal: показывает ролик в цветных ASCII-символах. Первые четыре секунды исходника пропускаются автоматически.

## Запуск на Windows

1. Установи Python 3.10 или новее.
2. Склонируй репозиторий:

   ```cmd
   git clone https://github.com/HolyStarik/Rick-Edit.git
   cd Rick-Edit
   ```

3. Запусти `run.cmd`. При первом запуске скрипт установит нужные Python-библиотеки.

Видео `rick_edit.mp4` уже лежит рядом со скриптом. Чтобы запустить другой файл, перетащи его на `run.cmd`.

Остановка — `Ctrl+C`. Можно менять `--width` и `--fps` в `run.cmd`, чтобы подстроить размер и плавность под экран ноутбука.

## Ручной запуск

```cmd
python -m pip install -r requirements.txt
python ascii_video.py "rick_edit.mp4" --start 4 --color
```

Если используешь другой ролик, укажи его путь вместо `rick_edit.mp4`.

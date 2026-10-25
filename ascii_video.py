#!/usr/bin/env python3
"""Play a local video as colored ASCII art in a Windows terminal."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

import imageio_ffmpeg
from PIL import Image


PALETTE = " .,:;irsXA253hMHGS#9B&@"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Показывает видео символами в CMD или Windows Terminal."
    )
    parser.add_argument("video", type=Path, help="путь к исходному видео")
    parser.add_argument("--start", type=float, default=4.0,
                        help="с какого времени начать, в секундах (по умолчанию: 4)")
    parser.add_argument("--width", type=int, default=96,
                        help="ширина рисунка в символах (по умолчанию: 96)")
    parser.add_argument("--fps", type=float, default=12.0,
                        help="частота проигрывания (по умолчанию: 12)")
    parser.add_argument("--color", action="store_true",
                        help="показывать символы в цвете (может работать медленнее)")
    return parser.parse_args()


def to_ascii(frame: bytes, size: tuple[int, int], width: int, color: bool) -> list[str]:
    source = Image.frombytes("RGB", size, frame)
    height = max(1, round(width * size[1] / size[0] * 0.48))
    image = source.resize((width, height), Image.Resampling.BILINEAR)
    pixels = list(image.getdata())
    rows: list[str] = []
    for y in range(height):
        parts: list[str] = []
        for x in range(width):
            r, g, b = pixels[y * width + x]
            light = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            char = PALETTE[min(len(PALETTE) - 1, int(light * (len(PALETTE) - 1)))]
            if color:
                parts.append(f"\x1b[38;2;{r};{g};{b}m{char}")
            else:
                parts.append(char)
        if color:
            parts.append("\x1b[0m")
        rows.append("".join(parts))
    return rows


def main() -> int:
    args = parse_args()
    if not args.video.is_file():
        print(f"Не найден файл: {args.video}", file=sys.stderr)
        return 2
    if args.start < 0 or args.width < 20 or args.fps <= 0:
        print("Проверьте параметры: --start >= 0, --width >= 20, --fps > 0.", file=sys.stderr)
        return 2

    # A modern Windows CMD/Windows Terminal supports ANSI sequences. Enable them
    # for older consoles when color was explicitly requested.
    if args.color and sys.platform == "win32":
        import os
        os.system("")

    try:
        reader = imageio_ffmpeg.read_frames(
            str(args.video), pix_fmt="rgb24", input_params=["-ss", str(args.start)]
        )
        metadata = next(reader)
    except Exception as exc:
        print(f"Не удалось открыть видео: {exc}", file=sys.stderr)
        return 1

    size = metadata["size"]
    source_fps = metadata.get("fps") or args.fps
    interval = 1.0 / args.fps
    next_frame_at = 0.0
    frame_number = 0
    terminal_height = shutil.get_terminal_size((120, 40)).lines
    print("Нажми Ctrl+C, чтобы остановить. Начинаю с отметки", args.start, "с.")
    time.sleep(1)
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()

    try:
        for frame in reader:
            timestamp = frame_number / source_fps
            frame_number += 1
            if timestamp + 1e-6 < next_frame_at:
                continue
            next_frame_at += interval
            rows = to_ascii(frame, size, args.width, args.color)
            # Keep output inside the visible console area.
            rows = rows[: max(1, terminal_height - 1)]
            sys.stdout.write("\x1b[H" + "\n".join(rows) + "\x1b[J")
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        reader.close()
        sys.stdout.write("\x1b[0m\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

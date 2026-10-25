#!/usr/bin/env python3
"""Loop a local video as colored ASCII art in the terminal."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

import imageio_ffmpeg
from PIL import Image


PALETTE = " .,:;irsXA253hMHGS#9B&@"
CELL_HEIGHT_RATIO = 0.48


def get_terminal_size():
    try:
        # Read the live TTY dimensions directly; COLUMNS/LINES can be stale.
        return os.get_terminal_size(sys.stdout.fileno())
    except OSError:
        return shutil.get_terminal_size((120, 40))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Показывает видео символами во весь экран терминала и повторяет его."
    )
    parser.add_argument("video", type=Path, help="путь к исходному видео")
    parser.add_argument("--start", type=float, default=4.0,
                        help="с какого времени начинать, в секундах (по умолчанию: 4)")
    parser.add_argument("--width", type=int,
                        help="максимальная ширина в символах; по умолчанию — весь терминал")
    parser.add_argument("--fit", choices=("stretch", "contain"), default="stretch",
                        help="stretch заполняет терминал растяжением; contain сохраняет пропорции")
    parser.add_argument("--fps", type=float, default=12.0,
                        help="частота проигрывания (по умолчанию: 12)")
    parser.add_argument("--color", action="store_true",
                        help="показывать символы в цвете")
    return parser.parse_args()


def fit_to_terminal(
    video_size: tuple[int, int],
    terminal_size: tuple[int, int],
    max_width: int | None,
    fit: str,
) -> tuple[int, int]:
    video_width, video_height = video_size
    columns, rows = terminal_size
    available_width = max(20, columns - 1)  # avoid terminal line wrapping
    available_height = max(1, rows)
    if max_width is not None:
        available_width = min(available_width, max_width)

    if fit == "stretch":
        return available_width, available_height

    width = min(available_width, max(1, int(
        available_height * video_width / video_height / CELL_HEIGHT_RATIO
    )))
    height = max(1, round(width * video_height / video_width * CELL_HEIGHT_RATIO))
    return width, min(height, available_height)


def to_ascii(
    frame: bytes, size: tuple[int, int], width: int, color: bool, target_height: int | None = None
) -> list[str]:
    source = Image.frombytes("RGB", size, frame)
    height = target_height or max(1, round(width * size[1] / size[0] * CELL_HEIGHT_RATIO))
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


def center_on_terminal(
    rows: list[str], terminal_width: int, terminal_height: int, frame_width: int
) -> str:
    frame_height = min(len(rows), terminal_height)
    vertical_padding = (terminal_height - frame_height) // 2
    horizontal_padding = max(0, (terminal_width - frame_width) // 2)
    blank = " " * max(0, terminal_width - 1)
    output = [blank] * vertical_padding
    output.extend((" " * horizontal_padding) + row for row in rows[:frame_height])
    output.extend([blank] * (terminal_height - len(output)))
    return "\n".join(output)


def draw_full_frame(picture: str) -> str:
    # Address every row directly and erase it first to prevent leftovers when
    # frame dimensions change or a line becomes shorter than the previous one.
    return "".join(
        f"\x1b[{row_number};1H\x1b[2K{line}"
        for row_number, line in enumerate(picture.split("\n"), start=1)
    )


def main() -> int:
    args = parse_args()
    if not args.video.is_file():
        print(f"Не найден файл: {args.video}", file=sys.stderr)
        return 2
    if args.start < 0 or (args.width is not None and args.width < 20) or args.fps <= 0:
        print("Проверьте параметры: --start >= 0, --width >= 20, --fps > 0.", file=sys.stderr)
        return 2

    if args.color and sys.platform == "win32":
        import os
        os.system("")

    terminal = get_terminal_size()
    columns, terminal_rows = terminal.columns, terminal.lines
    terminal_rows = max(1, terminal_rows)
    interval = 1.0 / args.fps
    screen_started = False

    try:
        # Use the alternate screen and hide the cursor for a clean full-screen player.
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H")
        sys.stdout.flush()
        screen_started = True

        while True:
            reader = None
            shown_frames = 0
            try:
                reader = imageio_ffmpeg.read_frames(
                    str(args.video), pix_fmt="rgb24", input_params=["-ss", str(args.start)]
                )
                metadata = next(reader)
                video_size = metadata["size"]
                source_fps = float(metadata.get("fps") or args.fps)
                next_frame_at = 0.0
                frame_number = 0
                cycle_started = time.monotonic()

                for frame in reader:
                    timestamp = frame_number / source_fps
                    frame_number += 1
                    if timestamp + 1e-6 < next_frame_at:
                        continue

                    # Re-read the dimensions so resizing the terminal takes effect live.
                    terminal = get_terminal_size()
                    columns, terminal_rows = terminal.columns, max(1, terminal.lines)
                    width, height = fit_to_terminal(
                        video_size, (columns, terminal_rows), args.width, args.fit
                    )
                    rows = to_ascii(frame, video_size, width, args.color, height)
                    picture = center_on_terminal(rows, columns, terminal_rows, width)
                    sys.stdout.write(draw_full_frame(picture))
                    sys.stdout.flush()
                    shown_frames += 1

                    next_frame_at += interval
                    deadline = cycle_started + next_frame_at
                    time.sleep(max(0.0, deadline - time.monotonic()))
            finally:
                if reader is not None:
                    reader.close()

            if shown_frames == 0:
                print(f"В видео нет кадров после отметки {args.start:g} с.", file=sys.stderr)
                return 1
            # EOF: reopen the source and begin again from --start.
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Не удалось воспроизвести видео: {exc}", file=sys.stderr)
        return 1
    finally:
        if screen_started:
            sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Defines some general-purpose utility functions."""

import datetime
import itertools
import logging
import re
import sys
from typing import Literal

RESET_SEQ = "\033[0m"
REG_COLOR_SEQ = "\033[%dm"
BOLD_COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

Color = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "grey",
    "light-red",
    "light-green",
    "light-yellow",
    "light-blue",
    "light-magenta",
    "light-cyan",
]

COLOR_INDEX: dict[Color, int] = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "grey": 90,
    "light-red": 91,
    "light-green": 92,
    "light-yellow": 93,
    "light-blue": 94,
    "light-magenta": 95,
    "light-cyan": 96,
}


def color_parts(color: Color, bold: bool = False) -> tuple[str, str]:
    if bold:
        return BOLD_COLOR_SEQ % COLOR_INDEX[color], RESET_SEQ
    return REG_COLOR_SEQ % COLOR_INDEX[color], RESET_SEQ


def uncolored(s: str) -> str:
    return re.sub(r"\033\[[\d;]+m", "", s)


def colored(s: str, color: Color | None = None, bold: bool = False) -> str:
    if color is None:
        return s
    start, end = color_parts(color, bold=bold)
    return start + s + end


def wrapped(
    s: str,
    length: int | None = None,
    space: str = " ",
    spaces: str | re.Pattern = r" ",
    newlines: str | re.Pattern = r"[\n\r]",
    too_long_suffix: str = "...",
    show_end: int | float | None = 0.5,
    max_lines: int | None = None,
) -> list[str]:
    strings = []
    lines = re.split(newlines, s.strip(), flags=re.MULTILINE | re.UNICODE)

    for line in lines:
        cur_string = []
        cur_length = 0

        for part in re.split(spaces, line.strip(), flags=re.MULTILINE | re.UNICODE):
            if length is None:
                cur_string.append(part)
                cur_length += len(space) + len(part)
            else:
                if len(part) > length:
                    if show_end is None:
                        part = part[: length - len(too_long_suffix)] + too_long_suffix
                    else:
                        if isinstance(show_end, float):
                            show_end = round(length * show_end)
                        part = (
                            part[: max(length - len(too_long_suffix) - show_end, 0)]
                            + too_long_suffix
                            + part[max(len(part) - show_end, 0) :]
                        )
                if cur_length + len(part) > length:
                    strings.append(space.join(cur_string))
                    cur_string = [part]
                    cur_length = len(part)
                else:
                    cur_string.append(part)
                    cur_length += len(space) + len(part)
        if cur_length > 0:
            strings.append(space.join(cur_string))

    if max_lines is not None:
        if max_lines < 1:
            raise ValueError("`max_lines` must be at least 1")
        if len(strings) > max_lines:
            strings = strings[-max_lines:]
            first_string, strings = strings[0], strings[1:]
            if length is not None and len(first_string) > length - len(too_long_suffix):
                first_string = first_string[len(too_long_suffix):]
            strings = [too_long_suffix + first_string] + strings[: max_lines - 1]

    return strings


def outlined(
    s: str,
    inner: Color | None = None,
    side: Color | None = None,
    bold: bool = False,
    max_length: int | None = None,
    space: str = " ",
    spaces: str | re.Pattern = r" ",
    newlines: str | re.Pattern = r"[\n\r]",
) -> str:
    strs = wrapped(uncolored(s), max_length, space, spaces, newlines)
    max_len = max(len(s) for s in strs)
    strs = [f"{s}{' ' * (max_len - len(s))}" for s in strs]
    strs = [colored(s, inner, bold=bold) for s in strs]
    strs_with_sides = [f"{colored('│', side)} {s} {colored('│', side)}" for s in strs]
    top = colored("┌─" + "─" * max_len + "─┐", side)
    bottom = colored("└─" + "─" * max_len + "─┘", side)
    return "\n".join([top] + strs_with_sides + [bottom])


def show_info(s: str, important: bool = False) -> None:
    if important:
        s = outlined(s, inner="light-cyan", side="cyan", bold=True)
    else:
        s = colored(s, "light-cyan", bold=False)
    sys.stdout.write(s)
    sys.stdout.write("\n")
    sys.stdout.flush()


def show_error(s: str, important: bool = False) -> None:
    if important:
        s = outlined(s, inner="light-red", side="red", bold=True)
    else:
        s = colored(s, "light-red", bold=False)
    sys.stdout.write(s)
    sys.stdout.write("\n")
    sys.stdout.flush()


def show_warning(s: str, important: bool = False) -> None:
    if important:
        s = outlined(s, inner="light-yellow", side="yellow", bold=True)
    else:
        s = colored(s, "light-yellow", bold=False)
    sys.stdout.write(s)
    sys.stdout.write("\n")
    sys.stdout.flush()


class TextBlock:
    def __init__(
        self,
        text: str,
        color: Color | None = None,
        bold: bool = False,
        width: int | None = None,
        space: str = " ",
        spaces: str | re.Pattern = r" ",
        newlines: str | re.Pattern = r"[\n\r]",
        too_long_suffix: str = "...",
        no_sep: bool = False,
        center: bool = False,
        show_end: int | float | None = 0.5,
        max_lines: int | None = None,
    ) -> None:
        super().__init__()

        self.width = width
        self.lines = wrapped(uncolored(text), width, space, spaces, newlines, too_long_suffix, show_end, max_lines)
        self.color = color
        self.bold = bold
        self.no_sep = no_sep
        self.center = center


def render_text_blocks(
    blocks: list[list[TextBlock]],
    newline: str = "\n",
    align_all_blocks: bool = False,
    padding: int = 0,
) -> str:
    """Renders a collection of blocks into a single string.

    Args:
        blocks: The blocks to render.
        newline: The string to use as a newline separator.
        align_all_blocks: If set, aligns the widths for all blocks.
        padding: The amount of padding to add to each block.

    Returns:
        The rendered blocks.
    """
    if align_all_blocks:
        if any(len(row) != len(blocks[0]) for row in blocks):
            raise ValueError("All rows must have the same number of blocks in order to align them")
        widths = [[max(len(line) for line in i.lines) if i.width is None else i.width for i in r] for r in blocks]
        row_widths = [max(i) for i in zip(*widths)]
        for row in blocks:
            for i, block in enumerate(row):
                block.width = row_widths[i]

    def get_widths(row: list[TextBlock], n: int = 0) -> list[int]:
        return [
            (max(len(line) for line in block.lines) if block.width is None else block.width) + n + padding
            for block in row
        ]

    def get_acc_widths(row: list[TextBlock], n: int = 0) -> list[int]:
        return list(itertools.accumulate(get_widths(row, n)))

    def get_height(row: list[TextBlock]) -> int:
        return max(len(block.lines) for block in row)

    def pad(s: str, width: int, center: bool) -> str:
        swidth = len(s)
        if center:
            lpad, rpad = (width - swidth) // 2, (width - swidth + 1) // 2
        else:
            lpad, rpad = 0, width - swidth
        return " " * lpad + s + " " * rpad

    lines = []
    prev_row: list[TextBlock] | None = None
    for row in blocks:
        if prev_row is None:
            lines += ["┌─" + "─┬─".join(["─" * width for width in get_widths(row)]) + "─┐"]
        elif not all(block.no_sep for block in row):
            ins, outs = get_acc_widths(prev_row, 3), get_acc_widths(row, 3)
            segs = sorted([(i, False) for i in ins] + [(i, True) for i in outs])
            line = ["├"]

            c = 1
            for i, (s, is_out) in enumerate(segs):
                if i > 0 and segs[i - 1][0] == s:
                    continue
                is_in_out = i < len(segs) - 1 and segs[i + 1][0] == s
                is_last = i == len(segs) - 2 if is_in_out else i == len(segs) - 1

                line += "─" * (s - c)
                if is_last:
                    if is_in_out:
                        line += "┤"
                    elif is_out:
                        line += "┐"
                    else:
                        line += "┘"
                else:  # noqa: PLR5501
                    if is_in_out:
                        line += "┼"
                    elif is_out:
                        line += "┬"
                    else:
                        line += "┴"
                c = s + 1

            lines += ["".join(line)]

        for i in range(get_height(row)):
            lines += [
                "│ "
                + " │ ".join(
                    [
                        (
                            " " * width
                            if i >= len(block.lines)
                            else colored(pad(block.lines[i], width, block.center), block.color, bold=block.bold)
                        )
                        for block, width in zip(row, get_widths(row))
                    ]
                )
                + " │"
            ]

        prev_row = row
    if prev_row is not None:
        lines += ["└─" + "─┴─".join(["─" * width for width in get_widths(prev_row)]) + "─┘"]

    return newline.join(lines)


def format_timedelta(timedelta: datetime.timedelta, short: bool = False) -> str:
    """Formats a delta time to human-readable format.

    Args:
        timedelta: The delta to format
        short: If set, uses a shorter format

    Returns:
        The human-readable time delta
    """
    parts = []
    if timedelta.days > 0:
        if short:
            parts += [f"{timedelta.days}d"]
        else:
            parts += [f"{timedelta.days} day" if timedelta.days == 1 else f"{timedelta.days} days"]

    seconds = timedelta.seconds

    if seconds > 60 * 60:
        hours, seconds = seconds // (60 * 60), seconds % (60 * 60)
        if short:
            parts += [f"{hours}h"]
        else:
            parts += [f"{hours} hour" if hours == 1 else f"{hours} hours"]

    if seconds > 60:
        minutes, seconds = seconds // 60, seconds % 60
        if short:
            parts += [f"{minutes}m"]
        else:
            parts += [f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"]

    if short:
        parts += [f"{seconds}s"]
    else:
        parts += [f"{seconds} second" if seconds == 1 else f"{seconds} seconds"]

    return ", ".join(parts)


class ColoredFormatter(logging.Formatter):
    """Defines a custom formatter for displaying logs."""

    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"

    COLORS: dict[str, Color] = {
        "WARNING": "yellow",
        "INFOALL": "magenta",
        "INFO": "cyan",
        "DEBUGALL": "grey",
        "DEBUG": "grey",
        "CRITICAL": "yellow",
        "FATAL": "red",
        "ERROR": "red",
    }

    def __init__(
        self,
        *,
        prefix: str | None = None,
        use_color: bool = True,
    ) -> None:
        asc_start, asc_end = color_parts("grey")
        name_start, name_end = color_parts("blue", bold=True)
        message_pre = [
            "{levelname:^19s}",
            asc_start,
            "{asctime}",
            asc_end,
            " [",
            name_start,
            "{name}",
            name_end,
            "]",
        ]
        message_post = [" {message}"]
        if prefix is not None:
            message_pre += [" ", colored(prefix, "magenta", bold=True)]
        message = "".join(message_pre + message_post)
        super().__init__(message, style="{", datefmt="%Y-%m-%d %H:%M:%S")

        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname

        match levelname:
            case "DEBUG":
                record.levelname = ""
            case "INFOALL":
                record.levelname = "INFO"
            case "DEBUGALL":
                record.levelname = "DEBUG"

        if record.levelname and self.use_color and levelname in self.COLORS:
            record.levelname = colored(record.levelname, self.COLORS[levelname], bold=True)
        return logging.Formatter.format(self, record)


def configure_logging(prefix: str | None = None) -> None:
    """Instantiates logging.

    Args:
        prefix: An optional prefix to add to the logger
    """
    root_logger = logging.getLogger()

    # Remove all existing handlers.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Captures warnings from the warnings module.
    logging.captureWarnings(True)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColoredFormatter(prefix=prefix))

    root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.INFO)

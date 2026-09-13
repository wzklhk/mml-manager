"""MML text parser shared by the web service and file converters."""

import re
from typing import Dict, Iterable, List, Optional, TextIO


def split_commands(text: str) -> Iterable[str]:
    """Yield every ADD/SET statement, ending only on an unquoted semicolon."""
    start_pattern = re.compile(r"(?im)(?:^|(?<=;))\s*(?:ADD|SET)\s+")
    position = 0
    while match := start_pattern.search(text, position):
        start = match.start()
        quote = None
        index = match.end()
        while index < len(text):
            char = text[index]
            if quote:
                if char == quote:
                    if index + 1 < len(text) and text[index + 1] == quote:
                        index += 2
                        continue
                    quote = None
                elif char == "\\" and index + 1 < len(text):
                    index += 2
                    continue
            elif char in ("'", '"'):
                quote = char
            elif char == ";":
                yield text[start : index + 1].strip()
                position = index + 1
                break
            index += 1
        else:
            position = len(text)


def split_commands_stream(stream: TextIO, chunk_size: int = 1024 * 1024) -> Iterable[str]:
    """Incrementally yield commands without retaining the complete input file."""
    start_pattern = re.compile(r"(?im)(?:^|(?<=;))\s*(?:ADD|SET)\s+")
    buffer = ""
    eof = False
    while not eof:
        chunk = stream.read(chunk_size)
        eof = not chunk
        buffer += chunk
        search_from = 0
        while match := start_pattern.search(buffer, search_from):
            start = match.start()
            quote = None
            index = match.end()
            while index < len(buffer):
                char = buffer[index]
                if quote:
                    if char == quote:
                        if index + 1 < len(buffer) and buffer[index + 1] == quote:
                            index += 2
                            continue
                        quote = None
                    elif char == "\\" and index + 1 < len(buffer):
                        index += 2
                        continue
                elif char in ("'", '"'):
                    quote = char
                elif char == ";":
                    yield buffer[start : index + 1].strip()
                    buffer = buffer[index + 1 :]
                    search_from = 0
                    break
                index += 1
            else:
                # Retain only the incomplete command for the next read.
                buffer = buffer[start:]
                break
        else:
            if not eof:
                # No command start is present. Keep enough tail for a start token
                # split across chunks, plus text following the latest newline.
                latest_line = buffer.rsplit("\n", 1)[-1]
                buffer = latest_line[-32:]


def parse_mml_stream(stream: TextIO) -> Iterable[Dict]:
    """Parse a text stream one command at a time."""
    for command in split_commands_stream(stream):
        parsed = parse_any_command(command)
        if parsed:
            yield parsed


def parse_key_value_pairs(text: str) -> Dict[str, Optional[str]]:
    """Parse comma-separated KEY=VALUE pairs with single or double quoted values."""
    result: Dict[str, Optional[str]] = {}
    index = 0
    while index < len(text):
        while index < len(text) and (text[index].isspace() or text[index] == ","):
            index += 1
        key_start = index
        while index < len(text) and text[index] not in "=,":
            index += 1
        if index >= len(text) or text[index] != "=":
            break
        key = text[key_start:index].strip()
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1

        if index < len(text) and text[index] in ("'", '"'):
            quote = text[index]
            index += 1
            chars: List[str] = []
            while index < len(text):
                char = text[index]
                if char == quote:
                    if index + 1 < len(text) and text[index + 1] == quote:
                        chars.append(quote)
                        index += 2
                        continue
                    index += 1
                    break
                if char == "\\" and index + 1 < len(text) and text[index + 1] == quote:
                    chars.append(quote)
                    index += 2
                    continue
                chars.append(char)
                index += 1
            value = "".join(chars)
            while index < len(text) and text[index] != ",":
                index += 1
        else:
            value_start = index
            while index < len(text) and text[index] != ",":
                index += 1
            value = text[value_start:index].strip()
        if key:
            result[key] = value if value != "" else None
    return result


def parse_any_command(command: str) -> Optional[Dict]:
    match = re.match(r"^\s*(ADD|SET)\s+([^:]+?)\s*:\s*(.*?)\s*;\s*$", command, re.I | re.S)
    if not match:
        return None
    return {
        "cmd_type": match.group(1).upper(),
        "table": " ".join(match.group(2).split()),
        "values": parse_key_value_pairs(match.group(3)),
    }


def parse_mml_text(text: str) -> Dict[str, List[Dict]]:
    tables: Dict[str, List[Dict]] = {}
    for command in split_commands(text):
        parsed = parse_any_command(command)
        if parsed:
            tables.setdefault(parsed["table"], []).append(parsed)
    return tables

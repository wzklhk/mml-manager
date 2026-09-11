"""Compatibility wrappers around the shared MML parser."""

from ..mml_parser import parse_any_command, parse_key_value_pairs, parse_mml_text


def parse_mml_file(file_path: str, encoding: str = "utf-8"):
    with open(file_path, "r", encoding=encoding) as handle:
        return parse_mml_text(handle.read())

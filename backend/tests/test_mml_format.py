import math

from app.mml_parser import parse_mml_text
from app.utils.mml import format_mml_command, quote_mml_value


def test_format_mml_command_uses_json_scalar_format():
    command = format_mml_command(
        "SET",
        "CELL",
        {
            "ID": 1,
            "POWER": -2.5,
            "ENABLED": True,
            "EMPTY": None,
            "CODE": "001",
            "NAME": 'A "quoted" value',
            "PATH": r"C:\temp\file",
        },
    )

    assert command == (
        'SET CELL:ID=1,POWER=-2.5,ENABLED=true,EMPTY=null,CODE="001",NAME="A \\"quoted\\" value",'
        'PATH="C:\\\\temp\\\\file";'
    )
    assert parse_mml_text(command)["CELL"][0]["values"] == {
        "ID": 1,
        "POWER": -2.5,
        "ENABLED": True,
        "EMPTY": None,
        "CODE": "001",
        "NAME": 'A "quoted" value',
        "PATH": r"C:\temp\file",
    }


def test_non_json_values_are_exported_as_strings():
    assert quote_mml_value(math.nan) == '"nan"'

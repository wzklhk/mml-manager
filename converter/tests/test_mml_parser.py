from converter.mml_parser import parse_mml_text


def test_parses_all_add_and_set_forms_with_quoted_delimiters():
    text = """
    ignored preamble
    ADD SFTP SERVER USER:NAME='admin user',NOTE='comma, semicolon; equals=ok';
    SET NAT SWITCH:
      NATSWITCH="ON MODE",DESC="A ""quoted"" value";
    ADD EMPTY VALUES:ONE='',TWO=""; SET SAME LINE:ID=1;
    """

    tables = parse_mml_text(text)

    assert set(tables) == {"SFTP SERVER USER", "NAT SWITCH", "EMPTY VALUES", "SAME LINE"}
    assert tables["SFTP SERVER USER"][0] == {
        "cmd_type": "ADD",
        "table": "SFTP SERVER USER",
        "values": {"NAME": "admin user", "NOTE": "comma, semicolon; equals=ok"},
    }
    assert tables["NAT SWITCH"][0]["values"] == {
        "NATSWITCH": "ON MODE",
        "DESC": 'A "quoted" value',
    }
    assert tables["EMPTY VALUES"][0]["values"] == {"ONE": None, "TWO": None}
    assert tables["SAME LINE"][0]["values"] == {"ID": "1"}


def test_ignores_non_add_set_statements_and_unterminated_commands():
    tables = parse_mml_text("RMV CELL:ID=1;\nSET VALID:ID=2;\nADD BROKEN:ID=3")
    assert list(tables) == ["VALID"]

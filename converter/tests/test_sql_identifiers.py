import sqlite3

from converter.converters.mml_to_sql import generate_create_table_sql, generate_insert_sql, generate_sql_script
from converter.services.mml import import_mml_file
from converter.services.memory_store import store


def test_generated_sql_supports_table_names_with_spaces():
    table_name = "SFTP SERVER USER"
    columns = ["NFSNAME", "USER NAME"]
    create_sql = generate_create_table_sql(table_name, columns)
    insert_sql, values = generate_insert_sql(
        table_name, {"NFSNAME": "node-1", "USER NAME": "admin"}, for_sql_file=False
    )

    db = sqlite3.connect(":memory:")
    db.execute(create_sql)
    db.execute(insert_sql, values)
    row = db.execute('SELECT "NFSNAME", "USER NAME" FROM "SFTP SERVER USER"').fetchone()

    assert row == ("node-1", "admin")


def test_complete_sql_script_quotes_dynamic_table_names():
    configs = {"NAT SWITCH": [{"cmd_type": "SET", "table": "NAT SWITCH", "values": {"NATSWITCH": "ON"}}]}
    statements = generate_sql_script(configs, {"NAT SWITCH": {"NATSWITCH"}})

    db = sqlite3.connect(":memory:")
    db.executescript("\n".join(statements))

    assert db.execute('SELECT "NATSWITCH" FROM "NAT SWITCH"').fetchone()[0] == "ON"


def test_mml_import_loads_commands_with_space_in_their_names_into_memory(tmp_path):
    source_path = tmp_path / "commands.txt"
    source_path.write_text(
        "SET NAT SWITCH:NATSWITCH=ON;\n" "SET SFTP SERVER USER:NFSNAME=node-1,USERNAME=admin;\n",
        encoding="utf-8",
    )
    result = import_mml_file(str(source_path))

    assert result["total_count"] == 2
    assert result["tables"] == ["NAT SWITCH", "SFTP SERVER USER"]
    tables, _ = store.snapshot()
    assert tables["NAT SWITCH"]["rows"][0]["values"] == {"NATSWITCH": "ON"}
    assert tables["SFTP SERVER USER"]["rows"][0]["cmd_type"] == "SET"

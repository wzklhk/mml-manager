import os
import tempfile
import unittest

from app.services import mml as mml_service
from app.services.mml import _parse_mml_text, compare_mml_files


class CompareMmlTests(unittest.TestCase):
    def _file(self, content, encoding="utf-8"):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mml")
        handle.write(content.encode(encoding))
        handle.close()
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    def test_detects_added_removed_and_field_changes(self):
        baseline = self._file("SET CELL:ID=1,NAME=A,POWER=40;\nSET CELL:ID=2,NAME=B,POWER=41;")
        target = self._file("SET CELL:ID=1,NAME=A,POWER=42;\nSET CELL:ID=3,NAME=C,POWER=41;")

        result = compare_mml_files(baseline, target)

        self.assertEqual(result["summary"], {"added": 1, "removed": 1, "modified": 1, "unchanged": 0})
        table = result["tables"][0]
        self.assertEqual(table["key_fields"], ["ID"])
        modified = next(diff for diff in table["diffs"] if diff["status"] == "modified")
        self.assertEqual(modified["changes"], [{"field": "POWER", "before": 40, "after": 42}])

    def test_supports_multiline_quoted_semicolon_and_gb18030(self):
        text = 'SET ROUTE:ID=1,\nNAME="核心;路由",DESC="A""B";'
        parsed = _parse_mml_text(text)
        self.assertEqual(parsed["ROUTE"][0]["values"]["NAME"], "核心;路由")
        self.assertEqual(parsed["ROUTE"][0]["values"]["DESC"], 'A"B')

        baseline = self._file(text, "gb18030")
        target = self._file(text.replace('DESC="A""B"', "DESC=C"), "gb18030")
        self.assertEqual(compare_mml_files(baseline, target)["summary"]["modified"], 1)

    def test_compares_two_persisted_configurations(self):
        baseline = mml_service.import_mml_text(
            'SET CELL:ID=1,CODE="001",POWER=40; SET CELL:ID=2,CODE="002",POWER=41;',
            "baseline.mml",
        )
        target = mml_service.import_mml_text(
            'SET CELL:ID=1,CODE="001",POWER=42; SET CELL:ID=3,CODE="003",POWER=41;',
            "target.mml",
        )

        result = mml_service.compare_snapshots(baseline["snapshot"]["id"], target["snapshot"]["id"])

        self.assertEqual(result["summary"], {"added": 1, "removed": 1, "modified": 1, "unchanged": 0})
        modified = next(diff for diff in result["tables"][0]["diffs"] if diff["status"] == "modified")
        self.assertEqual(modified["changes"], [{"field": "POWER", "before": 40, "after": 42}])

    def test_snapshot_comparison_requires_distinct_configurations(self):
        snapshot = mml_service.create_configuration("Empty")["snapshot"]
        with self.assertRaisesRegex(ValueError, "不同"):
            mml_service.compare_snapshots(snapshot["id"], snapshot["id"])


if __name__ == "__main__":
    unittest.main()

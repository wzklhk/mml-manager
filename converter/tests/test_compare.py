import os
import tempfile
import unittest

from converter.services.mml import _parse_mml_text, compare_mml_files


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
        self.assertEqual(modified["changes"], [{"field": "POWER", "before": "40", "after": "42"}])

    def test_supports_multiline_quoted_semicolon_and_gb18030(self):
        text = 'SET ROUTE:ID=1,\nNAME="核心;路由",DESC="A""B";'
        parsed = _parse_mml_text(text)
        self.assertEqual(parsed["ROUTE"][0]["values"]["NAME"], "核心;路由")
        self.assertEqual(parsed["ROUTE"][0]["values"]["DESC"], 'A"B')

        baseline = self._file(text, "gb18030")
        target = self._file(text.replace('DESC="A""B"', "DESC=C"), "gb18030")
        self.assertEqual(compare_mml_files(baseline, target)["summary"]["modified"], 1)


if __name__ == "__main__":
    unittest.main()

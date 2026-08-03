from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "import_google_trends.py"
SPEC = importlib.util.spec_from_file_location("import_google_trends", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TrendsImportTest(unittest.TestCase):
    def test_parse_interest_preserves_below_one_flag(self) -> None:
        self.assertEqual(MODULE.parse_interest("<1"), (0.5, True))
        self.assertEqual(MODULE.parse_interest("42"), (42.0, False))

    def test_find_header_skips_google_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "export.csv"
            path.write_text(
                "Category: All categories\nWeek,Ice cream: (Food)\n2021-01-03,25\n",
                encoding="utf-8",
            )
            self.assertEqual(MODULE.find_header_row(path), 1)


if __name__ == "__main__":
    unittest.main()

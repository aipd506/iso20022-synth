"""Unit tests for the isosynth CLI."""

import unittest
import tempfile
from pathlib import Path
from iso20022_synth.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_generate_and_validate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_pacs008.xml"

            # 1. Generate
            ret_gen = main(["generate", "pacs.008", "-c", "2", "--currency", "USD", "--amount", "1000", "-o", str(out_file)])
            self.assertEqual(ret_gen, 0)
            self.assertTrue(out_file.exists())

            # 2. Validate
            ret_val = main(["validate", str(out_file)])
            self.assertEqual(ret_val, 0)

            # 3. Inspect
            ret_ins = main(["inspect", str(out_file)])
            self.assertEqual(ret_ins, 0)


if __name__ == "__main__":
    unittest.main()

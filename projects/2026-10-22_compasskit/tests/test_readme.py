"""The README's library example is executed, so it cannot drift from the code."""

from __future__ import annotations

import contextlib
import io
import os
import re
import unittest

from tests.support import PKG_DIR

FENCE = "`" * 3


class ReadmeExample(unittest.TestCase):
    def test_library_example_runs(self):
        with open(os.path.join(PKG_DIR, "README.md"), encoding="utf-8") as fh:
            text = fh.read()
        blocks = re.findall(FENCE + "python\n(.*?)" + FENCE, text, re.S)
        self.assertTrue(blocks, "README has no python example")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(blocks[0], "README.md", "exec"), {})
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0].split()[0], "29")
        self.assertEqual(lines[1:], ["hypothetical False", "True", "ask"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

# Generated from notebooks/redesign/00_harness_and_audit.ipynb; edit the notebook, not this file.
"""노트북 추출의 경로·소유권·재현성을 임시 파일로 검증합니다."""

import json
import tempfile
import unittest
from pathlib import Path

from harness.notebook_tools import render_exports, sync_exports


class NotebookExportTests(unittest.TestCase):
    """파일 추출에서 보존해야 할 경계를 검증합니다."""

    def setUp(self):
        """각 테스트에 독립적인 임시 폴더를 만듭니다."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.nb = self.root / "example.ipynb"

    def notebook(self, target="harness/example.py", source="value = 1", extra=None):
        """지정한 목적지·코드로 작은 노트북을 만들어 경로를 반환합니다."""
        cells = [{"cell_type": "code", "metadata": {"tags": ["export"], "export_to": target},
                  "source": source}]
        cells.extend(extra or [])
        self.nb.write_text(json.dumps({"cells": cells}), encoding="utf-8")
        return self.nb

    def test_roundtrip_and_drift(self):
        """첫 쓰기 후 일치하며 수동 변경은 check에서 감지해야 합니다."""
        nb = self.notebook()
        self.assertEqual(sync_exports([nb], self.root), ["harness/example.py"])
        self.assertFalse((self.root / "harness").exists())
        sync_exports([nb], self.root, write=True)
        self.assertEqual(sync_exports([nb], self.root), [])
        target = self.root / "harness/example.py"
        target.write_text(target.read_text() + "value = 2\n")
        self.assertEqual(sync_exports([nb], self.root), ["harness/example.py"])

    def test_does_not_execute_and_skips_untagged(self):
        """예외를 던지는 셀도 문법만 검사하며 미지정 셀은 추출하지 않습니다."""
        nb = self.notebook(source="raise RuntimeError('must not execute')", extra=[
            {"cell_type": "code", "metadata": {}, "source": "not valid Python !"}])
        result = render_exports(nb, self.root)
        self.assertIn("raise RuntimeError", next(iter(result.values())))

    def test_blocks_unsafe_paths(self):
        """상위 경로·절대 경로·허용하지 않은 목적지를 거절합니다."""
        for target in ["../outside.py", str(self.root / "absolute.py"), ".env", "docs/x.py"]:
            with self.subTest(target=target), self.assertRaises(ValueError):
                render_exports(self.notebook(target), self.root)

    def test_preserves_manual_file(self):
        """소유권 표시 없는 기존 파일을 덮어쓰지 않습니다."""
        target = self.root / "harness/example.py"
        target.parent.mkdir()
        target.write_text("original = True")
        with self.assertRaises(ValueError):
            sync_exports([self.notebook()], self.root, write=True)
        self.assertEqual(target.read_text(), "original = True")

    def test_validates_all_before_writing(self):
        """뒤쪽 문법 오류가 앞 파일의 부분 갱신을 만들지 않습니다."""
        nb = self.notebook(extra=[{"cell_type": "code", "metadata": {
            "tags": ["export"], "export_to": "harness/broken.py"}, "source": "def broken("}])
        with self.assertRaises(SyntaxError):
            sync_exports([nb], self.root, write=True)
        self.assertFalse((self.root / "harness").exists())

    def test_duplicate_owners_and_missing_target(self):
        """중복 소유권·목적지 누락을 조용히 무시하지 않습니다."""
        nb = self.notebook()
        with self.assertRaises(ValueError):
            sync_exports([nb, nb], self.root, write=True)
        self.assertFalse((self.root / "harness").exists())
        with self.assertRaises(ValueError):
            render_exports(self.notebook(target=""), self.root)

    def test_multiple_cells_keep_order(self):
        """같은 목적지의 셀은 노트북 순서로 결합합니다."""
        nb = self.notebook(source="first = 1", extra=[{"cell_type": "code", "metadata": {
            "tags": ["export"], "export_to": "harness/example.py"}, "source": ["second = first + 1"]}])
        result = next(iter(render_exports(nb, self.root).values()))
        self.assertLess(result.index("first = 1"), result.index("second ="))

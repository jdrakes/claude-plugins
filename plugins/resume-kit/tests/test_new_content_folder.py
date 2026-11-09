"""Tests for skills/resume/bin/new-content-folder.

The starter folder is where a new user begins, so these check the layout
it creates, that it never writes into a folder that has something in it,
and, when typst and poppler are installed, that its example content builds
to one page without writing anything into the new folder.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / "skills" / "resume"
NEW_FOLDER = SKILL / "bin" / "new-content-folder"
BUILD = SKILL / "bin" / "build"
STARTER = SKILL / "starter"


def create(folder):
    return subprocess.run([str(NEW_FOLDER), str(folder)], capture_output=True, text=True)


def files_under(folder):
    return sorted(str(path.relative_to(folder)) for path in Path(folder).rglob("*"))


class LayoutTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)

    def test_a_new_folder_gets_the_starter_layout(self):
        folder = self.work / "alex"
        result = create(folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(files_under(folder),
                         ["CLAUDE.md", "KNOWLEDGE.md", "drafts", "resume-v1.yaml"])
        self.assertEqual((folder / "KNOWLEDGE.md").read_bytes(), b"")
        self.assertTrue((folder / "drafts").is_dir())
        self.assertEqual((folder / "resume-v1.yaml").read_bytes(),
                         (STARTER / "resume-v1.yaml").read_bytes())
        self.assertEqual((folder / "CLAUDE.md").read_bytes(),
                         (STARTER / "CLAUDE.template.md").read_bytes())

    def test_an_existing_empty_folder_is_used(self):
        folder = self.work / "alex"
        folder.mkdir()
        result = create(folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("resume-v1.yaml", files_under(folder))

    def test_a_folder_with_anything_in_it_is_refused(self):
        folder = self.work / "alex"
        folder.mkdir()
        (folder / "notes.txt").write_text("mine\n", encoding="utf-8")
        result = create(folder)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not empty", result.stderr)
        self.assertEqual(files_under(folder), ["notes.txt"])

    def test_a_file_in_the_way_is_refused(self):
        path = self.work / "alex"
        path.write_text("mine\n", encoding="utf-8")
        result = create(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a folder", result.stderr)
        self.assertEqual(path.read_text(encoding="utf-8"), "mine\n")

    def test_the_example_has_what_the_template_reads(self):
        data = yaml.safe_load((STARTER / "resume-v1.yaml").read_text(encoding="utf-8"))
        for key in ("name", "title", "summary"):
            self.assertTrue(data.get(key), key)
        for job in data["experience"]:
            for key in ("role", "company", "start", "bullets"):
                self.assertIn(key, job)


@unittest.skipUnless(all(shutil.which(tool) for tool in ("typst", "pdfinfo")),
                     "needs typst and pdfinfo")
class BuildTests(unittest.TestCase):
    def test_the_example_builds_to_one_page_outside_the_folder(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as temp_folder:
            folder = Path(work) / "alex"
            self.assertEqual(create(folder).returncode, 0)
            before = files_under(folder)
            result = subprocess.run(
                [str(BUILD), "resume-v1.yaml"], cwd=folder,
                env={**os.environ, "TMPDIR": temp_folder},
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(files_under(folder), before)
            info = subprocess.run(["pdfinfo", str(Path(temp_folder) / "resume-v1.pdf")],
                                  capture_output=True, text=True, check=True).stdout
            self.assertRegex(info, r"(?m)^Pages:\s+1$")


if __name__ == "__main__":
    unittest.main()
